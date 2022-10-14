# muesli/web/statements.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2022, Tobias Wackenhut <tobias (at) wackenhut.at>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sqlalchemy
from sqlalchemy import select, func, literal_column, union, union_all, and_, or_, not_, except_

from muesli import models as m
from typing import List


# Database select statements
# This file contains sqlalchemy statements in the new sqlalchemy 2.x style. The ones in models.py and some other parts
# of the codebase may still be in the old style. There is a deprecation warning, that can be enabled via environment
# variable to see which expressions are not converted to 2.x style yet. Look at the sqlalchemy documentation for that.

def lecture_registered_participants_stats_stmt(lecture_id: int) -> sqlalchemy.sql.expression.Select:
    # Number of students of each subject in a lecture
    # The outer join is necessary, because some people register without studying a subject
    participants_by_subject = select(literal_column("'participants'").label("type"),
                                     func.count(m.User.id),
                                     func.coalesce(m.Subject.name, '(Keine Angabe)')) \
        .join(m.LectureStudent) \
        .where(m.LectureStudent.lecture_id == lecture_id) \
        .outerjoin(m.user_subjects_table).outerjoin(m.Subject) \
        .group_by(m.Subject.name).order_by(m.Subject.name)

    # Subquery to check if a user has submitted a preference in this lecture
    user_has_prefs_in_lecture_subquery = select(m.TimePreference.student_id) \
        .where(m.TimePreference.lecture_id == lecture_id) \
        .where(m.TimePreference.student_id == m.User.id) \
        .exists()

    # Number of students of each subject being preliminary registered using preferences
    preliminary_participants_by_subject = select(literal_column("'preliminary_participants'").label("type"),
                                                 func.count(m.User.id),
                                                 func.coalesce(m.Subject.name, '(Keine Angabe)')) \
        .select_from(m.User) \
        .where(user_has_prefs_in_lecture_subquery) \
        .outerjoin(m.user_subjects_table).outerjoin(m.Subject) \
        .group_by(m.Subject.name).order_by(m.Subject.name)

    # Total number of registered students (real and preliminary)
    total_participants = select(literal_column("'participants'").label("type"),
                                func.count(m.LectureStudent.student_id),
                                literal_column("'TOTAL'").label("subject")) \
        .where(m.LectureStudent.lecture_id == lecture_id)

    total_preliminary_participants = select(literal_column("'preliminary_participants'").label("type"),
                                            func.count(m.User.id),
                                            literal_column("'TOTAL'").label("subject")) \
        .where(user_has_prefs_in_lecture_subquery)

    # Union of all the above statements to avoid multiple queries. We don't care about duplicates -> union_all instead
    # of union
    stmt = union_all(participants_by_subject, total_participants,
                     preliminary_participants_by_subject, total_preliminary_participants)
    return stmt


def lecture_registered_participants_stats(sa_session: sqlalchemy.orm.Session, lecture_id: int):
    registration_info = {}
    stmt = lecture_registered_participants_stats_stmt(lecture_id)
    for participation_type, count, subject_name in sa_session.execute(stmt):
        if subject_name == "TOTAL":
            registration_info[f"total_{participation_type}"] = count
            continue
        registration_info.setdefault(participation_type, {})[subject_name] = count
    return registration_info


def student_in_lecture_or_tutorials_existence_stmts(exam_id: int, tutorial_ids: List[int] = None) \
        -> dict[str, sqlalchemy.sql.expression.Select]:
    return {"TUTORIALS": select(m.LectureStudent.tutorial_id) \
                .where(m.LectureStudent.tutorial_id.in_(tutorial_ids)) \
                .where(m.LectureStudent.student_id == m.ExerciseStudent.student_id).exists(),
            "LECTURE": select(m.LectureStudent.lecture_id) \
                .where(m.LectureStudent.student_id == m.ExerciseStudent.student_id).exists()
            }


def lecture_exams_statistics_stmt(exam_id: int, tutorial_ids: List[int]=None) -> sqlalchemy.sql.expression.Select:
    # Get average of achieved points and standard deviation for every exercise in each exam of the lecture by each
    # course of studies.
    existence_statements = student_in_lecture_or_tutorials_existence_stmts(exam_id, tutorial_ids)

    def stats_subquery():
        # This is the core of this query. The statistics page requires the average, standard deviation and total for
        # different subsets of results: By subject and each lecture, total points achieved over all exercises by subject
        # and many more.
        # The same goes for the subset of students. Tutors should be able to compare their tutorial to the lecture
        # average. Therefor the query is done once for the whole lecture and again for only the students in selected
        # tutorials.
        #
        # This function implicitly takes the following arguments:
        # stats_type: Determines if the results to query are for all students in the lecture or only in selected
        # tutorials
        # by_exercise: Consider the sum over all exercises or every exercise individually
        # by_subject: Group by subject or ignore them (considering all students at once)
        res = select(
            literal_column(f"'{query_type}'"),
            literal_column("'TOTAL'") if not by_exercise else m.ExerciseStudent.exercise_id,
            m.Exercise.maxpoints,
            func.stddev_pop(m.ExerciseStudent.points),
            func.avg(m.ExerciseStudent.points),
            func.count(m.ExerciseStudent.student_id),
            literal_column("'TOTAL'") if not by_subjects else m.Subject.name
        ) \
        .join(m.Exercise).where(m.Exercise.exam_id == exam_id) \
        .where(existence_statements[query_type])

        if by_subjects:
            res = res.outerjoin(m.user_subjects_table).outerjoin(m.Subject) \
            .group_by(m.Subject.name).order_by(m.Subject.name)
        return res

    resulting_subqueries = []
    for query_type in ("LECTURE", "TUTORIALS"):
        for by_subjects in (True, False):
            for by_exercise in (True, False):
                resulting_subqueries.append(stats_subquery())


    stmt = union_all(*resulting_subqueries)
    #print(stmt)
    return stmt


# Execute the statistics query and return a dict. The dict can be used like this:
# exam_statistics["LECTURE"]["Mathematik (BSc. 100%)"]["Exercise 1"]["avg"]
# exam_statistics["TUTORIALS"]["TOTAL"]["TOTAL"]["stddev"]
def lecture_exams_statistics(sa_session: sqlalchemy.orm.Session, exam_id: int, tutorial_ids: List[int]=None):
    exam_statistics = {}
    stmt = lecture_exams_statistics_stmt(exam_id, tutorial_ids)
    for query_type, exercise_id, max_points, stddev, avg, count, subject_name in sa_session.execute(stmt):
        exam_statistics.setdefault(subject_name, {}).setdefault(exercise_id, {})[query_type] = {
            'max_points': max_points,
            'stddev': stddev,
            'avg': avg,
            'count': count
        }
    return exam_statistics


def exam_admission_registration_medical_count_stmt(exam_id: int, tutorial_ids: List[int]=None):
    existence_statements = student_in_lecture_or_tutorials_existence_stmts(exam_id, tutorial_ids)
    subqueries = []
    for query_type in ("LECTURE", "TUTORIALS"):
        # Number of admissions
        subqueries.append(select(literal_column(f"'{query_type}'"), literal_column("'ADMISSIONS'"), func.count(m.ExamAdmission.admission))\
            .where(m.ExamAdmission.admission == 1).where(m.ExamAdmission.exam_id == exam_id).where(existence_statements[query_type]))
        # Number of registrations
        subqueries.append(select(literal_column(f"'{query_type}'"), literal_column("'REGISTRATIONS'"), func.count(m.ExamAdmission.registration)) \
            .where(m.ExamAdmission.registration == 1).where(m.ExamAdmission.exam_id == exam_id).where(existence_statements[query_type]))
        # Number of registered and admitted participants
        subqueries.append(select(literal_column(f"'{query_type}'"), literal_column("'ADMITTED_AND_REGISTERED'"), func.count(m.ExamAdmission.registration)) \
                          .where(m.ExamAdmission.registration == 1).where(m.ExamAdmission.admission == 1).where(m.ExamAdmission.exam_id == exam_id).where(existence_statements[query_type]))
        # Number of medical certificates
        subqueries.append(select(literal_column(f"'{query_type}'"), literal_column("'MEDICAL_CERTIFICATES'"), func.count(m.ExamAdmission.medical_certificate)) \
            .where(m.ExamAdmission.medical_certificate == 1).where(m.ExamAdmission.exam_id == exam_id).where(existence_statements[query_type]))

    return union_all(*subqueries)


def exam_admission_registration_medical_count(sa_session: sqlalchemy.orm.Session, exam_id: int, tutorial_ids: List[int]=None):
    admission_counts = {}
    stmt = exam_admission_registration_medical_count_stmt(exam_id, tutorial_ids)
    for stats_type, stats_object, object_count in sa_session.execute(stmt):
        admission_counts.setdefault(stats_object, {})[stats_type] = object_count
    return admission_counts


def exam_result_percentiles_stmt(exam_id: int, tutorial_ids: List[int]=None) -> sqlalchemy.sql.expression.Select:
    existence_statements = student_in_lecture_or_tutorials_existence_stmts(exam_id, tutorial_ids)
    a = select(func.sum(m.ExerciseStudent.points).where(existence_statements['LECTURE']).join(m.Exercise).where(m.Exercise.exam_id == exam_id).group_by(m.ExerciseStudent.student))


def exam_result_percentiles(sa_session: sqlalchemy.orm.Session, exam_id: int, tutorial_ids: List[int]=None):
    percentiles = {}
    stmt = exam_result_percentiles_stmt(exam_id, tutorial_ids)
    return percentiles


def lecture_statistics_multi_semester_stmt(lecture_ids: List[int]):
    subqueries = []
    for lecture_id in lecture_ids:
        registrations = select(m.User.id.label("student_id")).join(m.LectureStudent).where(m.LectureStudent.lecture_id == lecture_id)
        past_registrations = select(m.User.id.label("student_id")).join(m.LectureRemovedStudent).where(m.LectureRemovedStudent.lecture_id == lecture_id)
        registered_students = union(registrations, past_registrations).subquery("registered_students")
        registered_count = select(func.count(registered_students.c.student_id)).select_from(registered_students).scalar_subquery()
        admitted_to_final_exam_query = select(m.ExamAdmission.student_id).join(m.Exam).where(m.ExamAdmission.admission == True).where(m.Exam.category == "exam").where(m.Exam.lecture_id == lecture_id).distinct()
        admitted_to_final_exam = admitted_to_final_exam_query.subquery("admitted")
        admitted_to_final_exam_count = select(func.count()).select_from(admitted_to_final_exam).scalar_subquery()

        student_exams_with_points = select(registered_students, m.Exam.id.label("exam_id")).select_from(registered_students).join(m.ExerciseStudent).join(m.Exercise).join(m.Exam).where(m.Exam.category == "assignment").where(m.Exam.lecture_id == lecture_id).group_by(registered_students.c.student_id, m.Exam.id).having(func.sum(m.ExerciseStudent.points) > 0).subquery("exams_with_points")
        active_students_query = select(student_exams_with_points.c.student_id).select_from(student_exams_with_points).group_by(student_exams_with_points.c.student_id).having(func.count(student_exams_with_points.c.exam_id)>=3)
        active_students = active_students_query.subquery("active_students")
        total_active_count = select(func.count()).select_from(active_students).scalar_subquery()
        active_faculty_internal = select(active_students.c.student_id).select_from(active_students).join(m.user_subjects_table, m.user_subjects_table.c.student == active_students.c.student_id).join(m.Subject).where(and_(
            or_(
                m.Subject.name.like('%athematik%'),
                m.Subject.name.like('%nformatik%'),
                m.Subject.name.like('%omputing%'),
                m.Subject.name.like('%omputer%'),
                m.Subject.name.like('%athics%'),

            ),
            not_(m.Subject.name.like('%linguistik%')),
            not_(m.Subject.name.like('%echnische%')),
            not_(m.Subject.name.like('%Wirtschaft%'))
        ))
        active_faculty_internal_count = select(func.count()).select_from(active_faculty_internal).scalar_subquery()
        active_faculty_external_count = select(func.count()).select_from(except_(active_students_query, active_faculty_internal)).scalar_subquery()
        admitted_repeaters_count = select(func.count()).select_from(except_(admitted_to_final_exam_query, active_students_query)).scalar_subquery()
        subqueries.append(select(m.Lecture.id, m.Lecture.term, m.Lecture.name, m.Lecture.lecturer, registered_count,
                                 admitted_to_final_exam_count, total_active_count, active_faculty_internal_count,
                                 active_faculty_external_count, admitted_repeaters_count) \
                          .where(m.Lecture.id == lecture_id))

    return union_all(*subqueries)
