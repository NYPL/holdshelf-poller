CREATE SCHEMA IF NOT EXISTS sierra_view;

DROP TABLE IF EXISTS sierra_view.hold;
CREATE TABLE sierra_view.hold (
  id BIGINT,
  record_id BIGINT,
  status CHARACTER(1),
  placed_gmt timestamp WITH TIME ZONE,
  pickup_location_code CHARACTER VARYING(5),
  patron_record_id BIGINT
);

DROP TABLE IF EXISTS sierra_view.item_view;
CREATE TABLE sierra_view.item_view (
  id BIGINT,
  record_num INTEGER,
  location_code CHARACTER VARYING(5)
);

DROP TABLE IF EXISTS sierra_view.patron_view;
CREATE TABLE sierra_view.patron_view (
  id BIGINT,
  record_num INTEGER
);
