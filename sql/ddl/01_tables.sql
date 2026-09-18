-- Star schema for HRRP readmissions. src/load.py rebuilds it on every run.
DROP TABLE IF EXISTS fact_readmission, dim_facility, dim_measure CASCADE;

CREATE TABLE dim_facility (
    facility_id        text PRIMARY KEY,
    facility_name      text NOT NULL,
    city               text,
    state              text NOT NULL,
    zip_code           text,
    county             text,
    hospital_type      text,
    hospital_ownership text,
    emergency_services boolean,
    overall_rating     smallint CHECK (overall_rating BETWEEN 1 AND 5),
    -- 'hrrp_fallback' rows exist only in the HRRP file, so their details are null
    record_source      text NOT NULL CHECK (record_source IN ('hospital_info', 'hrrp_fallback'))
);

CREATE TABLE dim_measure (
    measure_id     text PRIMARY KEY,
    measure_code   text NOT NULL UNIQUE,
    condition_name text NOT NULL
);

-- Grain: one row per facility, measure, and reporting period
CREATE TABLE fact_readmission (
    facility_id                text NOT NULL REFERENCES dim_facility,
    measure_id                 text NOT NULL REFERENCES dim_measure,
    start_date                 date NOT NULL,
    end_date                   date NOT NULL,
    number_of_discharges       integer,
    number_of_readmissions     integer,
    excess_readmission_ratio   numeric(7, 4),
    predicted_readmission_rate numeric(7, 4),
    expected_readmission_rate  numeric(7, 4),
    footnote                   smallint,
    is_suppressed              boolean NOT NULL,
    is_reported                boolean NOT NULL,
    PRIMARY KEY (facility_id, measure_id, start_date)
);
