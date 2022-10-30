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

"""Database select statements for various parts of MÜSLI.

This file contains sqlalchemy statements in the new sqlalchemy 2.x style. The ones in models.py and some other parts
of the codebase may still be in the old style. There is a deprecation warning, that can be enabled via environment
variable to see which expressions are not converted to 2.x style yet. Look at the sqlalchemy documentation for that.

Also contains convenience functions to execute the statements.

Typical usage example:
    statistics_data = statements.lecture_exams_statistics(request.db, exam.id, tutorials)
    print(statistics_data['LECTURE']['TOTAL'])
"""

import sqlalchemy.orm
from sqlalchemy import select, func, literal_column, union, union_all, and_, or_, not_, except_, true

from muesli import models as m
from typing import List


def lecture_registered_participants_stats_stmt(lecture_id: int) -> sqlalchemy.sql.expression.Select:
    """Number of students of each subject in a lecture.

    Builds select statement for lecture registrations by subject. The query result contains three columns:
    - type: One of 'participants', 'preliminary_participants'
    - count: Number of subscribed students in this metric
    - subject: One of some subject name, '(Keine Angabe)' or 'TOTAL'

    Args:
        lecture_id: Lecture id to build the statement for

    Returns:
        sqlalchemy 2.x style select statement generating a result explained above.
    """
    # The outer join is necessary, because some people register without studying a subject.
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
    """Execution function for the query build by lecture_registered_participant_stats_stmt.

    Args:
        sa_session: An sqlalchemy session
        lecture_id: Lecture id to query the metrics for

    Returns: A dict mapping from participation type to dict mappings from subject names to numbers of students. Where 
        participation type is one of 'participants', 'preliminary_participants'. Additional keys 'total_participants'
        and 'total_preliminary_participants' hold the total number of the corresponding registrations.
        For example:
        
        {
            "participants": {"Mathematics (B.Sc 100%)": 54, "Informatik (B.Sc 100%)": 11},
            "preliminary_participants: {},
            "total_participants: 65,
            "total_preliminary_participants: 0
        }
    """
    registration_info = {}
    stmt = lecture_registered_participants_stats_stmt(lecture_id)
    for participation_type, count, subject_name in sa_session.execute(stmt):
        if subject_name == "TOTAL":
            registration_info[f"total_{participation_type}"] = count
            continue
        registration_info.setdefault(participation_type, {})[subject_name] = count
    return registration_info


def student_subscribed_to_stmts(tutorial_ids: List[int]) -> dict[str, sqlalchemy.sql.expression.Select]:
    """Returns existence statements for checking, if a given ExerciseStudent object corresponds to a subscription to a
    lecture or tutorial.

    Example usage:
        existence_statements = student_subscribed_to_stmts([42])
        select(func.sum(m.ExerciseStudent.points)).where(existence_statements['LECTURE'])

    Args:
        tutorial_ids: List of tutorial ids for TUTORIALS type statement.

    Returns:
        A dict mapping from the string 'LECTURE' and optionally 'TUTORIALS' to a sqlalchemy exists query.
    """
    stmts = {
        "LECTURE": select(m.LectureStudent.lecture_id).where(
            m.LectureStudent.student_id == m.ExerciseStudent.student_id).exists()
    }
    if tutorial_ids:
        stmts['TUTORIALS'] = select(m.LectureStudent.tutorial_id).where(
            m.LectureStudent.tutorial_id.in_(tutorial_ids)).where(
            m.LectureStudent.student_id == m.ExerciseStudent.student_id).exists()
    return stmts


def lecture_exams_statistics_stmt(exam_id: int, tutorial_ids: List[int] = None) -> sqlalchemy.sql.expression.Select:
    """Constructs query for exam statistics.

    Generates a query to get the average of achieved points and standard deviation for every exercise in each exam of
    the lecture grouped by course of studies. The resulting query has 7 columns:
    - query type: one of 'LECTURE', 'TUTORIALS'
    - exercise_id: An exercise id or 0 (total identifier)
    - maxpoints: maximum number of points possible in this exercise
    - stddev: standard deviation of results
    - avg: average of results
    - count: number of students with points
    - subject: name of a subject or 'TOTAL'

    Args:
        exam_id: Exam id to calculate statistics for
        tutorial_ids: List of tutorial ids to calculate tutorial statistics for. Optional.
                      If not given, no tutorial metrics are calculated

    Returns:
        A sqlalchemy 2.x style select statement generating a result explained above.
    """
    existence_statements = student_subscribed_to_stmts(tutorial_ids)

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
        res = (select(literal_column(f"'{query_type}'"),
                      literal_column("0") if not by_exercise else m.ExerciseStudent.exercise_id,
                      m.Exercise.maxpoints,
                      func.stddev_pop(m.ExerciseStudent.points),
                      func.avg(m.ExerciseStudent.points),
                      func.count(m.ExerciseStudent.student_id),
                      literal_column("'TOTAL'") if not by_subjects else m.Subject.name)
               .join(m.Exercise)
               .where(m.Exercise.exam_id == exam_id)
               .where(existence_statements[query_type]))

        if by_subjects:
            res = (res.outerjoin(m.user_subjects_table, m.ExerciseStudent.student_id == m.user_subjects_table.c.student)
                   .outerjoin(m.Subject))
            if by_exercise:
                res = res.group_by(m.Subject.name, m.ExerciseStudent.exercise_id, m.Exercise.maxpoints)
            else:
                res = res.group_by(m.Subject.name, m.Exercise.maxpoints)
            res = res.order_by(m.Subject.name)
        else:
            res = res.group_by(m.ExerciseStudent.exercise_id, m.Exercise.maxpoints)
        return res

    resulting_subqueries = []
    query_types = ('LECTURE', 'TUTORIALS') if tutorial_ids else ('LECTURE',)
    for query_type in query_types:
        for by_subjects in (True, False):
            for by_exercise in (True, False):
                resulting_subqueries.append(stats_subquery())

    stmt = union_all(*resulting_subqueries)
    return stmt


def lecture_exams_statistics(sa_session: sqlalchemy.orm.Session, exam_id: int, tutorial_ids: List[int] = None):
    """Execution function for the query build by lecture_exams_statistics_stmt.

    Args:
        sa_session: An sqlalchemy session
        exam_id: Lecture id to query the metrics for
        tutorial_ids: Optional list of tutorial ids. An additional set of statistics will be calculated over all
                      students subscribed any of those tutorials.

    Returns: A nested dict mapping of the following form:

        {query_type: {subject_name: {exercise_title: {metric: value}}}}

        query_type: One of 'LECTURE', 'TUTORIALS'
        subject_name: Name of a subject or 'TOTAL'
        exercise_title: Name of an exercise or 'TOTAL'
        metric: One of 'max_points', 'stddev', 'avg', 'count'

        Example Usage:
            exam_statistics = lecture_exams_statistics(sa_session, 42, [63, 14])
            exam_statistics["LECTURE"]["Mathematik (BSc. 100%)"]["Exercise 1"]["avg"]
            exam_statistics["TUTORIALS"]["TOTAL"]["TOTAL"]["stddev"]
    """
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


def exam_admission_registration_medical_count_stmt(exam_id: int, tutorial_ids: List[int] = None):
    """Generates select statement for number of exam admissions, registrations and medical certificates

    Resulting query generates the following columns:
    - query_type: One of 'LECTURE', 'TUTORIALS'
    - metric: 'ADMISSIONS', 'REGISTRATIONS', 'ADMITTED_AND_REGISTERED', 'MEDICAL_CERTIFICATES'
    - count: Number of elements

    Args:
        exam_id: Exam id to calculate the counts for.
        tutorial_ids: Optional list of tutorial ids. If specified an additional set of metrics will be calculated over
                      all students subscribed to any of those tutorials.

    Returns:
        A sqlalchemy 2.x style select statement generating a result explained above.
    """
    existence_statements = student_subscribed_to_stmts(tutorial_ids)
    subqueries = []
    for query_type in ("LECTURE", "TUTORIALS") if tutorial_ids else ("LECTURE",):

        # Number of admissions
        subqueries.append(select(literal_column(f"'{query_type}'"), literal_column("'ADMISSIONS'"),
                                 func.count(m.ExamAdmission.admission))
                          .where(m.ExamAdmission.admission == true())
                          .where(m.ExamAdmission.exam_id == exam_id)
                          .where(existence_statements[query_type]))

        # Number of registrations
        subqueries.append(select(literal_column(f"'{query_type}'"), literal_column("'REGISTRATIONS'"),
                                 func.count(m.ExamAdmission.registration))
                          .where(m.ExamAdmission.registration == true())
                          .where(m.ExamAdmission.exam_id == exam_id)
                          .where(existence_statements[query_type]))

        # Number of registered and admitted participants
        subqueries.append(select(literal_column(f"'{query_type}'"), literal_column("'ADMITTED_AND_REGISTERED'"),
                                 func.count(m.ExamAdmission.registration))
                          .where(m.ExamAdmission.registration == true())
                          .where(m.ExamAdmission.admission == true())
                          .where(m.ExamAdmission.exam_id == exam_id)
                          .where(existence_statements[query_type]))

        # Number of medical certificates
        subqueries.append(select(literal_column(f"'{query_type}'"), literal_column("'MEDICAL_CERTIFICATES'"),
                                 func.count(m.ExamAdmission.medical_certificate))
                          .where(m.ExamAdmission.medical_certificate == true())
                          .where(m.ExamAdmission.exam_id == exam_id)
                          .where(existence_statements[query_type]))

    return union_all(*subqueries)


def exam_admission_registration_medical_count(sa_session: sqlalchemy.orm.Session, exam_id: int,
                                              tutorial_ids: List[int] = None):
    """Execution function for the query build by exam_admission_registration_medical_count_stmt.

    Args:
        sa_session: An sqlalchemy session
        exam_id: Lecture id to query the metrics for
        tutorial_ids: Optional list of tutorial ids. An additional set of statistics will be calculated over all
                      students subscribed any of those tutorials.

    Returns: A nested dict mapping of the following form:

        {metric: {query_type: count}}

        metric: One of 'ADMISSIONS', 'REGISTRATIONS', 'ADMITTED_AND_REGISTERED', 'MEDICAL_CERTIFICATES'
        query_type: One of 'LECTURE', 'TUTORIALS'
        count: Number of elements

        Example Usage:
            admission_registration_count = exam_admission_registration_medical_count(sa_session, 42, [63, 14])
            print(admission_registration_count['ADMISSIONS']['LECTURE'])
            print(admission_registration_count['MEDICAL_CERTIFICATES']['TUTORIALS'])
    """
    admission_counts = {}
    stmt = exam_admission_registration_medical_count_stmt(exam_id, tutorial_ids)
    for query_type, metric, metric_value in sa_session.execute(stmt):
        admission_counts.setdefault(metric, {})[query_type] = metric_value
    return admission_counts


def lecture_statistics_multi_semester_stmt(lecture_ids: List[int]):
    """Generates select query for the number of students achieving milestones in lectures.

    The query results in the following columns:

    lecture_id: Lecture id for this metric.
    lecture_term: Term the lecture is offered in.
    lecture_name: Title of the lecture.
    lecture_lecturer: Name of the lecturer.
    registered_count: Number of students registered to a tutorial.
    admitted_to_final_exam_count: Number of students admitted to any exam of this lecture.
    total_active_count: Number of students achieving points on at least 3 exams (i.e. exercise sheets).
    active_faculty_internal_count: Students of total_active_counts studying a subject offered by our faculty.
    active_faculty_external_count: Students of total_active_counts not studying any subject offered by our faculty.
    admitted_repeaters_count: Not active students admitted to exam. Most likely having an admission from previous term.

    Note, that the sum of admitted students external and internal always adds up to the total even if students have
    more than one subject. In case they study a subject from our faculty and another, they are still counted as internal
    faculty members.

    Args:
        lecture_ids: List of ids of lectures to calculate the metrics for.

    Returns:
        A sqlalchemy 2.x style select statement generating a result explained above.
    """
    subqueries = []
    for lecture_id in lecture_ids:

        registrations = (select(m.User.id.label("student_id"))
                         .join(m.LectureStudent)
                         .where(m.LectureStudent.lecture_id == lecture_id))

        past_registrations = (select(m.User.id.label("student_id"))
                              .join(m.LectureRemovedStudent)
                              .where(m.LectureRemovedStudent.lecture_id == lecture_id))

        registered_students = union(registrations, past_registrations).subquery("registered_students")

        registered_count = (select(func.count(registered_students.c.student_id))
                            .select_from(registered_students)
                            .scalar_subquery())

        admitted_to_final_exam_query = (select(m.ExamAdmission.student_id)
                                        .join(m.Exam)
                                        .where(m.ExamAdmission.admission == true())
                                        .where(m.Exam.category == "exam")
                                        .where(m.Exam.lecture_id == lecture_id)
                                        .distinct())

        admitted_to_final_exam = admitted_to_final_exam_query.subquery("admitted")
        admitted_to_final_exam_count = select(func.count()).select_from(admitted_to_final_exam).scalar_subquery()

        student_exams_with_points = (select(registered_students, m.Exam.id.label("exam_id"))
                                     .select_from(registered_students)
                                     .join(m.ExerciseStudent)
                                     .join(m.Exercise)
                                     .join(m.Exam)
                                     .where(m.Exam.category == "assignment")
                                     .where(m.Exam.lecture_id == lecture_id)
                                     .group_by(registered_students.c.student_id, m.Exam.id)
                                     .having(func.sum(m.ExerciseStudent.points) > 0)
                                     .subquery("exams_with_points"))

        active_students_query = (select(student_exams_with_points.c.student_id)
                                 .select_from(student_exams_with_points)
                                 .group_by(student_exams_with_points.c.student_id)
                                 .having(func.count(student_exams_with_points.c.exam_id) >= 3))

        active_students = active_students_query.subquery("active_students")
        total_active_count = select(func.count()).select_from(active_students).scalar_subquery()

        active_faculty_internal = (
            select(active_students.c.student_id)
            .select_from(active_students)
            .join(m.user_subjects_table, m.user_subjects_table.c.student == active_students.c.student_id)
            .join(m.Subject)
            .where(and_(or_(
                            m.Subject.name.like('%athematik%'),
                            m.Subject.name.like('%nformatik%'),
                            m.Subject.name.like('%omputing%'),
                            m.Subject.name.like('%omputer%'),
                            m.Subject.name.like('%athics%')
                        ),
                        not_(m.Subject.name.like('%linguistik%')),
                        not_(m.Subject.name.like('%echnische%')),
                        not_(m.Subject.name.like('%Wirtschaft%'))))
        )

        active_faculty_internal_count = (select(func.count())
                                         .select_from(active_faculty_internal)
                                         .scalar_subquery())

        active_faculty_external_count = (select(func.count())
                                         .select_from(except_(active_students_query, active_faculty_internal))
                                         .scalar_subquery())

        admitted_repeaters_count = (select(func.count())
                                    .select_from(except_(admitted_to_final_exam_query, active_students_query))
                                    .scalar_subquery())

        subqueries.append(select(m.Lecture.id, m.Lecture.term, m.Lecture.name, m.Lecture.lecturer, registered_count,
                                 admitted_to_final_exam_count, total_active_count, active_faculty_internal_count,
                                 active_faculty_external_count, admitted_repeaters_count)
                          .where(m.Lecture.id == lecture_id))

    return union_all(*subqueries)


def exam_points_quantils_stmt(exam_id: int, tutorial_ids: List[int] = None) -> sqlalchemy.sql.expression.Select:
    """Generates query for exam points and quantils.

    By design this function does not calculate common quantils for values like 0.5, as this is intended as a guideline
    for lecturers to set grade limits. Instead, it calculates any reached sum of points that has been reached by a
    student and determines the percentage of all possible points this represents, the number of students that have also
    reached at least that many points and what quantile this represents.

    The resulting query has 4 columns:

    query_type: 'ALL' or 'TUTORIALS'. The group the count and quantil metrics are calculated for
    point_sum: Number of points reached
    percentage: What fraction of the possible points this represents
    student_count: How many students have reached this number of points (all students or tutorial)
    quantils: Fraction of students reached this number of points.

    Args:
        exam_id: Exam id to calculate the counts for.
        tutorial_ids: Optional list of tutorial ids. If specified an additional set of metrics will be calculated over
                      all students subscribed to any of those tutorials.

    Returns:
        A sqlalchemy 2.x style select statement generating a result explained above.
    """
    # We need: lecture and tutorials statistics
    max_point_sum = (select(func.sum(m.Exercise.maxpoints))
                     .join(m.Exam)
                     .where(m.Exam.id == exam_id)
                     .scalar_subquery())

    subqueries = []

    query_types = ('ALL', 'TUTORIALS') if tutorial_ids else ('ALL',)
    for query_type in query_types:
        considered_student_ids_subquery = (select(m.LectureStudent.student_id)
                                           .join(m.Exam, m.Exam.lecture_id == m.LectureStudent.lecture_id)
                                           .where(m.Exam.id == exam_id))
        if query_type == 'TUTORIALS':
            given_student_in_tutorials_exists_subquery = (union(select(m.LectureStudent.student_id)
                                                                .where(m.LectureStudent.tutorial_id.in_(tutorial_ids)),
                                                                select(m.LectureRemovedStudent.student_id)
                                                                .where(m.LectureRemovedStudent.tutorial_id.in_(
                                                                    tutorial_ids)
                                                                       )).exists())
            considered_student_ids_subquery = (considered_student_ids_subquery
                                               .where(given_student_in_tutorials_exists_subquery))

        considered_student_ids_subquery = considered_student_ids_subquery.subquery()
        considered_student_ids_alias = considered_student_ids_subquery.alias()
        considered_student_count = select(func.count(considered_student_ids_alias.c.student_id)).scalar_subquery()

        sums_of_points_subquery = (
            select(func.sum(m.ExerciseStudent.points).label('point_sum'), m.ExerciseStudent.student_id)
            .join(considered_student_ids_subquery,
                  considered_student_ids_subquery.c.student_id == m.ExerciseStudent.student_id)
            .group_by(m.ExerciseStudent.student_id)
            .subquery()
        )

        # result_subquery = (select(sums_of_points_subquery, func.count(m.ExerciseStudent.student_id))
        #                    .where(considered_student_ids_subquery)
        #                    .where(sums_of_points_subquery.))
        sums_of_points_alias = sums_of_points_subquery.alias()
        number_of_students_with_leq_points = (
            select(func.count(sums_of_points_alias.c.student_id))
            .where(sums_of_points_alias.c.point_sum <= sums_of_points_subquery.c.point_sum)
            .scalar_subquery())

        this_query_type_result = (
            select(literal_column(f"'{query_type}'"),
                   sums_of_points_subquery.c.point_sum,
                   sums_of_points_subquery.c.point_sum / max_point_sum,
                   number_of_students_with_leq_points,
                   number_of_students_with_leq_points / considered_student_count
                   )
        )

        subqueries.append(this_query_type_result)

    stmt = union_all(*subqueries)
    return stmt.order_by(stmt.c.point_sum)


def exam_points_quantils(sa_session: sqlalchemy.orm.Session, exam_id: int, tutorial_ids: List[int] = None):
    percentiles = []
    stmt = exam_points_quantils_stmt(exam_id, tutorial_ids)
    for query_type, points, percentage, student_count, quantile in sa_session.execute(stmt):
        if points is None:
            continue
        if not percentiles or points != percentiles[-1][0]:
            percentiles.append(({
                'min_points': points,
                'min_percent': percentage
            }, {query_type: {
                'count': student_count,
                'quantile': quantile
            }}))
        else:
            percentiles[-1][1][query_type] = {
                'count': student_count,
                'quantile': quantile
            }
    for _, metrics in percentiles:
        if 'TUTORIALS' not in metrics:
            metrics['TUTORIALS'] = metrics['ALL']
    return percentiles
