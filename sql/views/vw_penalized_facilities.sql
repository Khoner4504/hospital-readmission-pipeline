-- (a) Facilities penalized per measure: excess readmission ratio above 1.0,
-- i.e. more readmissions than expected. CMS's actual payment penalty compares
-- each hospital with its peer-group median rather than a flat 1.0, so treat
-- this as a proxy.
CREATE OR REPLACE VIEW vw_penalized_facilities AS
SELECT f.facility_id,
       d.facility_name,
       d.city,
       d.state,
       d.hospital_type,
       d.record_source,
       m.measure_code,
       m.condition_name,
       f.excess_readmission_ratio,
       f.predicted_readmission_rate,
       f.expected_readmission_rate,
       f.number_of_discharges,
       f.number_of_readmissions,
       f.is_suppressed
FROM fact_readmission f
JOIN dim_facility d USING (facility_id)
JOIN dim_measure m USING (measure_id)
WHERE f.excess_readmission_ratio > 1.0;
