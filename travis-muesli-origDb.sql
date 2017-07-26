--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.3
-- Dumped by pg_dump version 9.6.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: beaker_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE beaker_cache (
    namespace character varying(255) NOT NULL,
    accessed timestamp without time zone NOT NULL,
    created timestamp without time zone NOT NULL,
    data bytea NOT NULL
);


ALTER TABLE beaker_cache OWNER TO postgres;

--
-- Name: confirmations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE confirmations (
    hash character varying(40) NOT NULL,
    "user" integer NOT NULL,
    source text NOT NULL,
    what text,
    created_on timestamp without time zone NOT NULL
);


ALTER TABLE confirmations OWNER TO postgres;

--
-- Name: exam_admissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE exam_admissions (
    exam integer NOT NULL,
    student integer NOT NULL,
    admission boolean,
    registration boolean,
    medical_certificate boolean
);


ALTER TABLE exam_admissions OWNER TO postgres;

--
-- Name: exams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE exams (
    id integer NOT NULL,
    lecture integer,
    name text,
    category text NOT NULL,
    admission boolean,
    registration boolean,
    medical_certificate boolean,
    url text,
    results_hidden boolean
);


ALTER TABLE exams OWNER TO postgres;

--
-- Name: exams_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE exams_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE exams_id_seq OWNER TO postgres;

--
-- Name: exams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE exams_id_seq OWNED BY exams.id;


--
-- Name: exercise_students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE exercise_students (
    exercise integer NOT NULL,
    student integer NOT NULL,
    points numeric(8,1)
);


ALTER TABLE exercise_students OWNER TO postgres;

--
-- Name: exercises; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE exercises (
    id integer NOT NULL,
    exam integer,
    nr integer NOT NULL,
    maxpoints numeric(8,1) NOT NULL
);


ALTER TABLE exercises OWNER TO postgres;

--
-- Name: exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE exercises_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE exercises_id_seq OWNER TO postgres;

--
-- Name: exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE exercises_id_seq OWNED BY exercises.id;


--
-- Name: grading_exams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE grading_exams (
    grading integer NOT NULL,
    exam integer NOT NULL
);


ALTER TABLE grading_exams OWNER TO postgres;

--
-- Name: gradings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE gradings (
    id integer NOT NULL,
    lecture integer NOT NULL,
    name text,
    formula text,
    hispos_type text,
    hispos_date text,
    examiner_id text
);


ALTER TABLE gradings OWNER TO postgres;

--
-- Name: gradings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE gradings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE gradings_id_seq OWNER TO postgres;

--
-- Name: gradings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE gradings_id_seq OWNED BY gradings.id;


--
-- Name: lecture_assistants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE lecture_assistants (
    lecture integer NOT NULL,
    assistant integer NOT NULL
);


ALTER TABLE lecture_assistants OWNER TO postgres;

--
-- Name: lecture_removed_students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE lecture_removed_students (
    lecture integer NOT NULL,
    student integer NOT NULL,
    tutorial integer
);


ALTER TABLE lecture_removed_students OWNER TO postgres;

--
-- Name: lecture_students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE lecture_students (
    lecture integer NOT NULL,
    student integer NOT NULL,
    tutorial integer
);


ALTER TABLE lecture_students OWNER TO postgres;

--
-- Name: lecture_tutors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE lecture_tutors (
    lecture integer NOT NULL,
    tutor integer NOT NULL
);


ALTER TABLE lecture_tutors OWNER TO postgres;

--
-- Name: lectures; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE lectures (
    id integer NOT NULL,
    assistant integer,
    name text,
    type text NOT NULL,
    term character varying(5),
    lsf_id text,
    lecturer text,
    url text,
    password text,
    is_visible boolean NOT NULL,
    mode text NOT NULL,
    minimum_preferences integer,
    tutor_rights text NOT NULL
);


ALTER TABLE lectures OWNER TO postgres;

--
-- Name: lectures_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE lectures_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE lectures_id_seq OWNER TO postgres;

--
-- Name: lectures_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE lectures_id_seq OWNED BY lectures.id;


--
-- Name: student_grades; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE student_grades (
    grading integer NOT NULL,
    student integer NOT NULL,
    grade numeric(2,1),
    CONSTRAINT student_grades_grade_check CHECK (((grade >= 1.0) AND (grade <= 5.0)))
);


ALTER TABLE student_grades OWNER TO postgres;

--
-- Name: time_preferences; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE time_preferences (
    lecture integer NOT NULL,
    student integer NOT NULL,
    "time" character varying(7) NOT NULL,
    penalty integer
);


ALTER TABLE time_preferences OWNER TO postgres;

--
-- Name: tutorial_preferences; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE tutorial_preferences (
    lecture integer NOT NULL,
    student integer NOT NULL,
    tutorial integer NOT NULL,
    penalty integer
);


ALTER TABLE tutorial_preferences OWNER TO postgres;

--
-- Name: tutorials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE tutorials (
    id integer NOT NULL,
    lecture integer,
    tutor integer,
    place text,
    max_students integer NOT NULL,
    comment text,
    "time" character varying(7),
    date date,
    is_special boolean NOT NULL
);


ALTER TABLE tutorials OWNER TO postgres;

--
-- Name: tutorials_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tutorials_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE tutorials_id_seq OWNER TO postgres;

--
-- Name: tutorials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tutorials_id_seq OWNED BY tutorials.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE users (
    id integer NOT NULL,
    email character varying(100) NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    password text,
    matrikel text,
    birth_date text,
    birth_place text,
    subject text,
    second_subject text,
    title text,
    is_admin integer NOT NULL,
    is_assistant integer NOT NULL
);


ALTER TABLE users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: exams id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exams ALTER COLUMN id SET DEFAULT nextval('exams_id_seq'::regclass);


--
-- Name: exercises id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exercises ALTER COLUMN id SET DEFAULT nextval('exercises_id_seq'::regclass);


--
-- Name: gradings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY gradings ALTER COLUMN id SET DEFAULT nextval('gradings_id_seq'::regclass);


--
-- Name: lectures id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lectures ALTER COLUMN id SET DEFAULT nextval('lectures_id_seq'::regclass);


--
-- Name: tutorials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tutorials ALTER COLUMN id SET DEFAULT nextval('tutorials_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Data for Name: beaker_cache; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY beaker_cache (namespace, accessed, created, data) FROM stdin;
954f49634d9546e0a1a5301968e8dbb0	2017-07-26 19:02:29.53619	2017-07-26 19:02:29.15067	\\x80027d7101550773657373696f6e7d710228550b617574682e75736572696471034a87060100550e5f61636365737365645f74696d6571044741d65e32c960ea57550e5f6372656174696f6e5f74696d6571054741d65e32c948fe8b55075f63737266745f7106582800000036373039386239396162303234623033633831643638623137366132333864373961393462623235710775732e
\.


--
-- Data for Name: confirmations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY confirmations (hash, "user", source, what, created_on) FROM stdin;
b2f1ae65a84224f60c3fea9170fcd950734d80cd	67201	user/register	\N	2017-07-26 19:02:28.922528
\.


--
-- Data for Name: exam_admissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY exam_admissions (exam, student, admission, registration, medical_certificate) FROM stdin;
\.


--
-- Data for Name: exams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY exams (id, lecture, name, category, admission, registration, medical_certificate, url, results_hidden) FROM stdin;
13415	20109	Aufgabenblatt 1	assignment	\N	\N	\N	\N	f
13416	20109	Aufgabenblatt 2	assignment	\N	\N	\N	\N	f
\.


--
-- Name: exams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('exams_id_seq', 13416, true);


--
-- Data for Name: exercise_students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY exercise_students (exercise, student, points) FROM stdin;
\.


--
-- Data for Name: exercises; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY exercises (id, exam, nr, maxpoints) FROM stdin;
6723	13415	1	4.0
\.


--
-- Name: exercises_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('exercises_id_seq', 6723, true);


--
-- Data for Name: grading_exams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY grading_exams (grading, exam) FROM stdin;
6692	13415
\.


--
-- Data for Name: gradings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY gradings (id, lecture, name, formula, hispos_type, hispos_date, examiner_id) FROM stdin;
6692	20109	Endnote	\N	\N	\N	\N
\.


--
-- Name: gradings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('gradings_id_seq', 6692, true);


--
-- Data for Name: lecture_assistants; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY lecture_assistants (lecture, assistant) FROM stdin;
20109	67205
20110	67206
20111	67205
\.


--
-- Data for Name: lecture_removed_students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY lecture_removed_students (lecture, student, tutorial) FROM stdin;
\.


--
-- Data for Name: lecture_students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY lecture_students (lecture, student, tutorial) FROM stdin;
20109	67198	46839
20109	67199	46842
\.


--
-- Data for Name: lecture_tutors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY lecture_tutors (lecture, tutor) FROM stdin;
20109	67204
20109	67203
\.


--
-- Data for Name: lectures; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY lectures (id, assistant, name, type, term, lsf_id, lecturer, url, password, is_visible, mode, minimum_preferences, tutor_rights) FROM stdin;
20109	\N	Irgendwas	lecture	\N	\N	\N	\N	geheim	t	direct	\N	editOwnTutorial
20110	\N	Irgendwas2	lecture	\N	\N	\N	\N	\N	t	off	\N	editOwnTutorial
20111	\N	Vorlieben	lecture	\N	\N	\N	\N	\N	t	prefs	\N	editOwnTutorial
\.


--
-- Name: lectures_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('lectures_id_seq', 20111, true);


--
-- Data for Name: student_grades; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY student_grades (grading, student, grade) FROM stdin;
\.


--
-- Data for Name: time_preferences; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY time_preferences (lecture, student, "time", penalty) FROM stdin;
20111	67198	0 14:00	1
\.


--
-- Data for Name: tutorial_preferences; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY tutorial_preferences (lecture, student, tutorial, penalty) FROM stdin;
\.


--
-- Data for Name: tutorials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY tutorials (id, lecture, tutor, place, max_students, comment, "time", date, is_special) FROM stdin;
46838	20110	67203	In einer weiter entfernten Galaxis	42	\N	0 14:00	\N	f
46839	20109	67203	In einer weit entfernten Galaxis	42	\N	0 12:00	\N	f
46840	20109	67204	In einer noch weiter entfernten Galaxis	42	\N	0 16:00	\N	f
46841	20109	\N	In einer noch viel weiter entfernten Galaxis	42	\N	0 18:00	\N	f
46842	20109	67203	In einer weit entfernten Galaxis	42	\N	0 14:00	\N	f
46843	20111	67204	In einer weit entfernten Galaxis	42	\N	0 14:00	\N	f
46844	20111	67204	In einer weiter entfernten Galaxis	42	\N	0 16:00	\N	f
\.


--
-- Name: tutorials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('tutorials_id_seq', 46844, true);


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY users (id, email, first_name, last_name, password, matrikel, birth_date, birth_place, subject, second_subject, title, is_admin, is_assistant) FROM stdin;
67207	admin@muesli.org	Anton	Admin	efacc4001e857f7eba4ae781c2932dedf843865e	2613945	\N		Mathematik (BSc)			1	0
67198	user@muesli.org	Stefan	Student	c73ba2982c55b7ead0e4098a92f722bdb3a3b3d8	\N	\N	\N	Mathematik (BSc)	\N	\N	0	0
67199	user2@muesli.org	Sigmund	Student	bd63afe0b3aae9a85c7675a1d989dbca5173abae	\N	\N	\N	Mathematik (MSc)	\N	\N	0	0
67200	user_without_lecture@muesli.org	Sebastian	Student	341b837c4300466034eacf88eae22824df7ea507	\N	\N	\N	Mathematik (MSc)	\N	\N	0	0
67201	user_unconfirmed@muesli.org	Ulrich	Student	\N	\N	\N	\N	\N	\N	\N	0	0
67202	unicodeuser@muesli.org	Uli	Unicode	a9946740136442bf7b585747cf2cd871ccd38731	\N	\N	\N	Mathematik (MSc)	\N	\N	0	0
67203	tutor@muesli.org	Thorsten	Tutor	1e6f622411e5941b720091e34d7182037dbb7135	\N	\N	\N	Mathematik (Dipl.)	\N	\N	0	0
67204	tutor2@muesli.org	Thor2sten	Tu2tor	e6d751291b25123d4da3794212021582f2704f83	\N	\N	\N	Mathematik (BSc)	\N	\N	0	0
67205	assistant@muesli.org	Armin	Assistent	8951365cbe9bc4d747c779d342598e29d06615d4	\N	\N	\N	Mathematik (BSc)	\N	\N	0	1
67206	assistant2@muesli.org	Armin	Assistent2	c8582b7fae27d83a0af8469228d62ad7df7b1996	\N	\N	\N	Mathematik (BSc)	\N	\N	0	1
\.


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('users_id_seq', 67207, true);


--
-- Name: beaker_cache beaker_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY beaker_cache
    ADD CONSTRAINT beaker_cache_pkey PRIMARY KEY (namespace);


--
-- Name: confirmations confirmations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY confirmations
    ADD CONSTRAINT confirmations_pkey PRIMARY KEY (hash);


--
-- Name: exam_admissions exam_admissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exam_admissions
    ADD CONSTRAINT exam_admissions_pkey PRIMARY KEY (exam, student);


--
-- Name: exams exams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exams
    ADD CONSTRAINT exams_pkey PRIMARY KEY (id);


--
-- Name: exercise_students exercise_students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exercise_students
    ADD CONSTRAINT exercise_students_pkey PRIMARY KEY (exercise, student);


--
-- Name: exercises exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exercises
    ADD CONSTRAINT exercises_pkey PRIMARY KEY (id);


--
-- Name: grading_exams grading_exams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY grading_exams
    ADD CONSTRAINT grading_exams_pkey PRIMARY KEY (grading, exam);


--
-- Name: gradings gradings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY gradings
    ADD CONSTRAINT gradings_pkey PRIMARY KEY (id);


--
-- Name: lecture_assistants lecture_assistants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_assistants
    ADD CONSTRAINT lecture_assistants_pkey PRIMARY KEY (lecture, assistant);


--
-- Name: lecture_removed_students lecture_removed_students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_removed_students
    ADD CONSTRAINT lecture_removed_students_pkey PRIMARY KEY (lecture, student);


--
-- Name: lecture_students lecture_students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_students
    ADD CONSTRAINT lecture_students_pkey PRIMARY KEY (lecture, student);


--
-- Name: lecture_tutors lecture_tutors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_tutors
    ADD CONSTRAINT lecture_tutors_pkey PRIMARY KEY (lecture, tutor);


--
-- Name: lectures lectures_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lectures
    ADD CONSTRAINT lectures_pkey PRIMARY KEY (id);


--
-- Name: student_grades student_grades_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY student_grades
    ADD CONSTRAINT student_grades_pkey PRIMARY KEY (grading, student);


--
-- Name: time_preferences time_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY time_preferences
    ADD CONSTRAINT time_preferences_pkey PRIMARY KEY (lecture, student, "time");


--
-- Name: tutorial_preferences tutorial_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tutorial_preferences
    ADD CONSTRAINT tutorial_preferences_pkey PRIMARY KEY (lecture, student, tutorial);


--
-- Name: tutorials tutorials_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tutorials
    ADD CONSTRAINT tutorials_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: confirmations confirmations_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY confirmations
    ADD CONSTRAINT confirmations_user_fkey FOREIGN KEY ("user") REFERENCES users(id) ON DELETE CASCADE;


--
-- Name: exam_admissions exam_admissions_exam_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exam_admissions
    ADD CONSTRAINT exam_admissions_exam_fkey FOREIGN KEY (exam) REFERENCES exams(id);


--
-- Name: exam_admissions exam_admissions_student_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exam_admissions
    ADD CONSTRAINT exam_admissions_student_fkey FOREIGN KEY (student) REFERENCES users(id);


--
-- Name: exams exams_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exams
    ADD CONSTRAINT exams_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id);


--
-- Name: exercise_students exercise_students_exercise_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exercise_students
    ADD CONSTRAINT exercise_students_exercise_fkey FOREIGN KEY (exercise) REFERENCES exercises(id);


--
-- Name: exercise_students exercise_students_student_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exercise_students
    ADD CONSTRAINT exercise_students_student_fkey FOREIGN KEY (student) REFERENCES users(id);


--
-- Name: exercises exercises_exam_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY exercises
    ADD CONSTRAINT exercises_exam_fkey FOREIGN KEY (exam) REFERENCES exams(id);


--
-- Name: grading_exams grading_exams_exam_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY grading_exams
    ADD CONSTRAINT grading_exams_exam_fkey FOREIGN KEY (exam) REFERENCES exams(id) ON DELETE CASCADE;


--
-- Name: grading_exams grading_exams_grading_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY grading_exams
    ADD CONSTRAINT grading_exams_grading_fkey FOREIGN KEY (grading) REFERENCES gradings(id) ON DELETE CASCADE;


--
-- Name: gradings gradings_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY gradings
    ADD CONSTRAINT gradings_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id);


--
-- Name: lecture_assistants lecture_assistants_assistant_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_assistants
    ADD CONSTRAINT lecture_assistants_assistant_fkey FOREIGN KEY (assistant) REFERENCES users(id) ON DELETE CASCADE;


--
-- Name: lecture_assistants lecture_assistants_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_assistants
    ADD CONSTRAINT lecture_assistants_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id) ON DELETE CASCADE;


--
-- Name: lecture_removed_students lecture_removed_students_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_removed_students
    ADD CONSTRAINT lecture_removed_students_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id);


--
-- Name: lecture_removed_students lecture_removed_students_student_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_removed_students
    ADD CONSTRAINT lecture_removed_students_student_fkey FOREIGN KEY (student) REFERENCES users(id);


--
-- Name: lecture_removed_students lecture_removed_students_tutorial_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_removed_students
    ADD CONSTRAINT lecture_removed_students_tutorial_fkey FOREIGN KEY (tutorial) REFERENCES tutorials(id);


--
-- Name: lecture_students lecture_students_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_students
    ADD CONSTRAINT lecture_students_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id);


--
-- Name: lecture_students lecture_students_student_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_students
    ADD CONSTRAINT lecture_students_student_fkey FOREIGN KEY (student) REFERENCES users(id);


--
-- Name: lecture_students lecture_students_tutorial_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_students
    ADD CONSTRAINT lecture_students_tutorial_fkey FOREIGN KEY (tutorial) REFERENCES tutorials(id);


--
-- Name: lecture_tutors lecture_tutors_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_tutors
    ADD CONSTRAINT lecture_tutors_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id);


--
-- Name: lecture_tutors lecture_tutors_tutor_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lecture_tutors
    ADD CONSTRAINT lecture_tutors_tutor_fkey FOREIGN KEY (tutor) REFERENCES users(id);


--
-- Name: lectures lectures_assistant_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY lectures
    ADD CONSTRAINT lectures_assistant_fkey FOREIGN KEY (assistant) REFERENCES users(id) ON DELETE SET NULL;


--
-- Name: student_grades student_grades_grading_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY student_grades
    ADD CONSTRAINT student_grades_grading_fkey FOREIGN KEY (grading) REFERENCES gradings(id);


--
-- Name: student_grades student_grades_student_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY student_grades
    ADD CONSTRAINT student_grades_student_fkey FOREIGN KEY (student) REFERENCES users(id);


--
-- Name: time_preferences time_preferences_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY time_preferences
    ADD CONSTRAINT time_preferences_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id);


--
-- Name: time_preferences time_preferences_student_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY time_preferences
    ADD CONSTRAINT time_preferences_student_fkey FOREIGN KEY (student) REFERENCES users(id);


--
-- Name: tutorial_preferences tutorial_preferences_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tutorial_preferences
    ADD CONSTRAINT tutorial_preferences_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id);


--
-- Name: tutorial_preferences tutorial_preferences_student_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tutorial_preferences
    ADD CONSTRAINT tutorial_preferences_student_fkey FOREIGN KEY (student) REFERENCES users(id);


--
-- Name: tutorial_preferences tutorial_preferences_tutorial_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tutorial_preferences
    ADD CONSTRAINT tutorial_preferences_tutorial_fkey FOREIGN KEY (tutorial) REFERENCES tutorials(id);


--
-- Name: tutorials tutorials_lecture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tutorials
    ADD CONSTRAINT tutorials_lecture_fkey FOREIGN KEY (lecture) REFERENCES lectures(id);


--
-- Name: tutorials tutorials_tutor_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tutorials
    ADD CONSTRAINT tutorials_tutor_fkey FOREIGN KEY (tutor) REFERENCES users(id);


--
-- PostgreSQL database dump complete
--

