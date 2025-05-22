/* create database*/
create database fic_data;

/*Create a new user (only with local access) and grant privileges to this user on the new database: */
CREATE USER 'fic_db_user'@'%' IDENTIFIED BY 'secret1234';
GRANT ALL PRIVILEGES ON fic_data.* TO 'fic_db_user'@'%';


/*After modifying the MariaDB grant tables, execute the following command in order to apply the changes:*/
flush privileges;

/*Change to the created database*/
use fic_data;

/*create table for storing device IDs*/
CREATE TABLE available_ids (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	logic_id varchar(50) NOT NULL,
 	is_assigned TINYINT,
 	UNIQUE (logic_id),
 	PRIMARY KEY (id)
 );

INSERT INTO available_ids (logic_id, is_assigned) VALUES ('tachograph_control_unit-1',0);
INSERT INTO available_ids (logic_id, is_assigned) VALUES ('tachograph_control_unit-2',0);
INSERT INTO available_ids (logic_id, is_assigned) VALUES ('tachograph_control_unit-3',0);
INSERT INTO available_ids (logic_id, is_assigned) VALUES ('tachograph_control_unit-4',0);

/*query over tachographs table*/
SELECT logic_id, is_assigned FROM available_ids ORDER BY logic_id DESC;

/*create table for storing vehicles identification information*/
CREATE TABLE tachographs (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	tachograph_id varchar(50) NOT NULL,
    tachograph_hostname varchar (50),
    telemetry_rate INT NOT NULL,
    sensors_sampling_rate float NOT NULL,
    status TINYINT,
 	UNIQUE (tachograph_id),
 	PRIMARY KEY (id)
 );

/*query over tachographs table*/
SELECT tachograph_id, tachograph_hostname, telemetry_rate, sensors_sampling_rate, status FROM tachographs ORDER BY tachograph_id DESC;;

/*create table for storing sessions identification information*/
CREATE TABLE sessions (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	session_id varchar(55) NOT NULL,
    tachograph_id varchar(50) NOT NULL,
    init_date timestamp NOT NULL,
    end_date timestamp,
    status TINYINT,
 	UNIQUE (session_id),
 	PRIMARY KEY (id)
 );

/*query over sessions table*/
SELECT session_id, tachograph_id, init_date, end_date, status FROM sessions ORDER BY init_date DESC;

/*create table for vehicles telemetry*/
CREATE TABLE telemetry (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	tachograph_id varchar(50) NOT NULL,
 	latitude float NOT NULL,
 	longitude float NOT NULL,
    gps_speed float NOT NULL,
 	current_speed float NOT NULL,
    current_driver_id varchar(50) NOT NULL,
 	time_stamp FLOAT8 NOT NULL,
 	PRIMARY KEY (id)
 );

/*query over table telemetry*/
SELECT tachograph_id, latitude, longitude, gps_speed, current_speed, current_driver_id, time_stamp
FROM telemetry ORDER BY tachograph_id DESC;

/*create table for vehicles events*/
CREATE TABLE events (
 	id MEDIUMINT NOT NULL AUTO_INCREMENT,
 	tachograph_id varchar(50) NOT NULL,
 	latitude float NOT NULL,
 	longitude float NOT NULL,
    warning varchar(100) NOT NULL,
 	time_stamp DATETIME NOT NULL,
 	PRIMARY KEY (id)
);


/*query over table vehicles events*/
SELECT tachograph_id, latitude, longitude, warning, time_stamp
FROM events ORDER BY tachograph_id DESC;