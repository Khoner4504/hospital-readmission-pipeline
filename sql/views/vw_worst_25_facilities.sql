-- (c) The 25 facilities with the highest excess readmission ratio nationally.
-- Each facility is ranked by its worst measure, so it appears only once.
CREATE OR REPLACE VIEW vw_worst_25_facilities AS
WITH per_facility AS (
    SELECT facility_id,
           max(excess_readmission_ratio) AS worst_excess_ratio,
           round(avg(excess_readmission_ratio), 4) AS avg_excess_ratio,
           count(*) AS reported_measures,
           count(*) FILTER (WHERE excess_readmission_ratio > 1.0) AS penalized_measures
    FROM fact_readmission
    WHERE is_reported
    GROUP BY facility_id
),
-- For each facility, keep only the measure with its highest ratio
worst_measure AS (
    SELECT DISTINCT ON (facility_id) facility_id, measure_id
    FROM fact_readmission
    WHERE is_reported
    ORDER BY facility_id, excess_readmission_ratio DESC, measure_id
)
SELECT row_number() OVER (ORDER BY p.worst_excess_ratio DESC, p.facility_id) AS national_rank,
       p.facility_id,
       d.facility_name,
       d.city,
       d.state,
       d.hospital_type,
       m.condition_name AS worst_condition,
       p.worst_excess_ratio,
       p.avg_excess_ratio,
       p.reported_measures,
       p.penalized_measures
FROM per_facility p
JOIN worst_measure w USING (facility_id)
JOIN dim_facility d USING (facility_id)
JOIN dim_measure m ON m.measure_id = w.measure_id
ORDER BY national_rank
LIMIT 25;
