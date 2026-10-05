-- PRAXIS product schema version 1. Apply to an empty database.
BEGIN;

CREATE TABLE product_audit (
	id VARCHAR(100) NOT NULL, 
	tenant_id VARCHAR(200) NOT NULL, 
	actor VARCHAR(200) NOT NULL, 
	event VARCHAR(100) NOT NULL, 
	resource_id VARCHAR(100), 
	correlation_id VARCHAR(100), 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id)
)

;

CREATE TABLE product_deliveries (
	event_id VARCHAR(100) NOT NULL, 
	tenant_id VARCHAR(200) NOT NULL, 
	payload JSON NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (event_id)
)

;

CREATE TABLE product_outbox (
	id VARCHAR(100) NOT NULL, 
	tenant_id VARCHAR(200) NOT NULL, 
	topic VARCHAR(100) NOT NULL, 
	payload JSON NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	attempts INTEGER NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	last_error TEXT, 
	PRIMARY KEY (id)
)

;

CREATE TABLE product_resources (
	tenant_id VARCHAR(200) NOT NULL, 
	kind VARCHAR(60) NOT NULL, 
	id VARCHAR(100) NOT NULL, 
	version INTEGER NOT NULL, 
	payload JSON NOT NULL, 
	created_at VARCHAR(40) NOT NULL, 
	PRIMARY KEY (tenant_id, kind, id, version)
)

;

CREATE TABLE product_schema_versions (
	version SERIAL NOT NULL, 
	PRIMARY KEY (version)
)

;
INSERT INTO product_schema_versions(version) VALUES (1);
COMMIT;
