-- Synthetic test referrals for the referral-loop diagnostic.
-- All rows tagged groupname='DIAG-TEST:<state>'. Remove with cleanup_test_referrals.sql.

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-09-29 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 0), 'admin', 'DIAG-TEST:missing_data', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-09-29'), (@tid, 'refer_to', 'Dermatology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', ''), (@tid, 'refer_diag', '');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-09-15 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 1), 'admin', 'DIAG-TEST:missing_data', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-09-15'), (@tid, 'refer_to', 'Neurology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', ''), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-08-14 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 2), 'admin', 'DIAG-TEST:missing_data', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-08-14'), (@tid, 'refer_to', 'Orthopedics'), (@tid, 'refer_from', 'admin'), (@tid, 'body', ''), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-08-24 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 3), 'admin', 'DIAG-TEST:missing_data', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-08-24'), (@tid, 'refer_to', 'Dermatology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', '');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-09-29 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 4), 'admin', 'DIAG-TEST:missing_data', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-09-29'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', ''), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-08-22 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 0), 'admin', 'DIAG-TEST:no_reply', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-08-22'), (@tid, 'refer_to', 'Gastroenterology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-07-11 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 1), 'admin', 'DIAG-TEST:no_reply', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-07-11'), (@tid, 'refer_to', 'Cardiology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-06-29 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 2), 'admin', 'DIAG-TEST:no_reply', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-06-29'), (@tid, 'refer_to', 'Gastroenterology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-08-23 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 3), 'admin', 'DIAG-TEST:no_reply', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-08-23'), (@tid, 'refer_to', 'Radiology-MRI'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-07-07 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 4), 'admin', 'DIAG-TEST:no_reply', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-07-07'), (@tid, 'refer_to', 'Radiology-CT'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-10-19 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 0), 'admin', 'DIAG-TEST:in_progress', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-10-19'), (@tid, 'refer_to', 'Neurology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-10-13 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 1), 'admin', 'DIAG-TEST:in_progress', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-10-13'), (@tid, 'refer_to', 'Orthopedics'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-10-15 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 2), 'admin', 'DIAG-TEST:in_progress', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-10-15'), (@tid, 'refer_to', 'Ophthalmology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-10-16 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 3), 'admin', 'DIAG-TEST:in_progress', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-10-16'), (@tid, 'refer_to', 'Orthopedics'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-10-18 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 4), 'admin', 'DIAG-TEST:in_progress', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-10-18'), (@tid, 'refer_to', 'Ophthalmology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-07-24 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 0), 'admin', 'DIAG-TEST:replied', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-07-24'), (@tid, 'refer_to', 'Dermatology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99'), (@tid, 'reply_date', '2026-08-03'), (@tid, 'reply_findings', 'Seen and assessed; see attached note');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-07-28 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 1), 'admin', 'DIAG-TEST:replied', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-07-28'), (@tid, 'refer_to', 'Ophthalmology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99'), (@tid, 'reply_date', '2026-08-23'), (@tid, 'reply_findings', 'Seen and assessed; see attached note');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-09-05 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 2), 'admin', 'DIAG-TEST:replied', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-09-05'), (@tid, 'refer_to', 'Neurology'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99'), (@tid, 'reply_date', '2026-10-05'), (@tid, 'reply_findings', 'Seen and assessed; see attached note');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-07-04 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 3), 'admin', 'DIAG-TEST:replied', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-07-04'), (@tid, 'refer_to', 'Radiology-CT'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99'), (@tid, 'reply_date', '2026-07-14'), (@tid, 'reply_findings', 'Seen and assessed; see attached note');

INSERT INTO transactions (date, title, pid, user, groupname, authorized) VALUES ('2026-08-31 09:00:00', 'LBTref', (SELECT pid FROM patient_data ORDER BY pid LIMIT 1 OFFSET 4), 'admin', 'DIAG-TEST:replied', 1);
SET @tid = LAST_INSERT_ID();
INSERT INTO lbt_data (form_id, field_id, field_value) VALUES (@tid, 'refer_date', '2026-08-31'), (@tid, 'refer_to', 'Radiology-MRI'), (@tid, 'refer_from', 'admin'), (@tid, 'body', 'Evaluate and treat'), (@tid, 'refer_diag', 'R99'), (@tid, 'reply_date', '2026-09-24'), (@tid, 'reply_findings', 'Seen and assessed; see attached note');
