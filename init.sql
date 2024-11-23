--
-- PostgreSQL database dump
--

-- Dumped from database version 14.13 (Ubuntu 14.13-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.13 (Ubuntu 14.13-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: prevent_default_config_deletion(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.prevent_default_config_deletion() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF OLD.name = 'default' THEN
        RAISE EXCEPTION 'Deletion of default configuration is not allowed';
    END IF;
    RETURN OLD;
END;
$$;


ALTER FUNCTION public.prevent_default_config_deletion() OWNER TO postgres;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: config; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.config (
    id integer NOT NULL,
    name character varying(100),
    provider_id integer NOT NULL,
    curl jsonb NOT NULL,
    tcping jsonb NOT NULL,
    nsi_option jsonb,
    system_option jsonb,
    monitor jsonb NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT config_name_check CHECK (((length((name)::text) >= 1) AND (length((name)::text) <= 100)))
);


ALTER TABLE public.config OWNER TO postgres;

--
-- Name: config_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.config_id_seq OWNER TO postgres;

--
-- Name: config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.config_id_seq OWNED BY public.config.id;


--
-- Name: ip_ranges; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ip_ranges (
    id integer NOT NULL,
    cidr character varying(45),
    start_ip character varying(45),
    end_ip character varying(45),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    provider_id integer NOT NULL,
    source character varying(45)
);


ALTER TABLE public.ip_ranges OWNER TO postgres;

--
-- Name: ip_ranges_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ip_ranges_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ip_ranges_id_seq OWNER TO postgres;

--
-- Name: ip_ranges_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ip_ranges_id_seq OWNED BY public.ip_ranges.id;


--
-- Name: ips; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ips (
    id bigint NOT NULL,
    ip_address character varying(45) NOT NULL,
    ip_type character varying(10) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    provider_id integer
);


ALTER TABLE public.ips OWNER TO postgres;

--
-- Name: ips_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ips_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ips_id_seq OWNER TO postgres;

--
-- Name: ips_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ips_id_seq OWNED BY public.ips.id;


--
-- Name: monitor; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.monitor (
    id integer NOT NULL,
    provider_id integer NOT NULL,
    enable boolean DEFAULT true NOT NULL
);


ALTER TABLE public.monitor OWNER TO postgres;

--
-- Name: monitor_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.monitor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.monitor_id_seq OWNER TO postgres;

--
-- Name: monitor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.monitor_id_seq OWNED BY public.monitor.id;


--
-- Name: provider_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.provider_id_seq OWNER TO postgres;

--
-- Name: providers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.providers (
    id integer DEFAULT nextval('public.provider_id_seq'::regclass) NOT NULL,
    name character varying(100) NOT NULL,
    api_url character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    logo_url character varying(255),
    deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public.providers OWNER TO postgres;

--
-- Name: test_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_results (
    id integer NOT NULL,
    ip character varying NOT NULL,
    avg_latency real,
    std_deviation real,
    packet_loss real,
    download_speed real,
    is_locked boolean DEFAULT false,
    status character varying(20),
    test_type character varying(10),
    test_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_delete boolean DEFAULT false
);


ALTER TABLE public.test_results OWNER TO postgres;

--
-- Name: test_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_results_id_seq OWNER TO postgres;

--
-- Name: test_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_results_id_seq OWNED BY public.test_results.id;


--
-- Name: config id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.config ALTER COLUMN id SET DEFAULT nextval('public.config_id_seq'::regclass);


--
-- Name: ip_ranges id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ip_ranges ALTER COLUMN id SET DEFAULT nextval('public.ip_ranges_id_seq'::regclass);


--
-- Name: ips id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ips ALTER COLUMN id SET DEFAULT nextval('public.ips_id_seq'::regclass);


--
-- Name: monitor id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monitor ALTER COLUMN id SET DEFAULT nextval('public.monitor_id_seq'::regclass);


--
-- Name: test_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_results ALTER COLUMN id SET DEFAULT nextval('public.test_results_id_seq'::regclass);


--
-- Name: config config_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.config
    ADD CONSTRAINT config_pkey PRIMARY KEY (id);


--
-- Name: ip_ranges ip_ranges_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ip_ranges
    ADD CONSTRAINT ip_ranges_pkey PRIMARY KEY (id);


--
-- Name: ips ips_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ips
    ADD CONSTRAINT ips_pkey PRIMARY KEY (id);


--
-- Name: monitor monitor_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monitor
    ADD CONSTRAINT monitor_pkey PRIMARY KEY (id);


--
-- Name: providers provider_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.providers
    ADD CONSTRAINT provider_pkey PRIMARY KEY (id);


--
-- Name: test_results test_results_Uni_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_results
    ADD CONSTRAINT "test_results_Uni_key" UNIQUE (ip);


--
-- Name: test_results test_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_results
    ADD CONSTRAINT test_results_pkey PRIMARY KEY (id);


--
-- Name: idx_provider_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_provider_id ON public.ips USING btree (provider_id);


--
-- Name: provder_id_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX provder_id_index ON public.ip_ranges USING btree (provider_id);


--
-- Name: config prevent_default_config_deletion_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER prevent_default_config_deletion_trigger BEFORE DELETE ON public.config FOR EACH ROW EXECUTE FUNCTION public.prevent_default_config_deletion();


--
-- Name: config update_config_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_config_updated_at BEFORE UPDATE ON public.config FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: ip_ranges fk_ip_ranges_provider; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ip_ranges
    ADD CONSTRAINT fk_ip_ranges_provider FOREIGN KEY (provider_id) REFERENCES public.providers(id) ON DELETE CASCADE;


--
-- Name: ips fk_ips_provider; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ips
    ADD CONSTRAINT fk_ips_provider FOREIGN KEY (provider_id) REFERENCES public.providers(id) ON DELETE CASCADE;


INSERT INTO public.config(
	 name, provider_id, curl, tcping, nsi_option, system_option, monitor, description)
	VALUES ('test', 32123312, '{"port": 443, "count": 5, "speed": 1, "enable": true, "time_out": 20, "download_url": "https://download.parallels.com/desktop/v17/17.1.1-51537/ParallelsDesktop-17.1.1-51537.dmg", "ip_v4_enable": true, "ip_v6_enable": false}','{"port": 443, "count": 30, "enable": true, "time_out": 20, "avg_latency": 200, "packet_loss": 0.25, "ip_v4_enable": true, "ip_v6_enable": false, "std_deviation": "200"}' , '{"avg_latency_weight": 0.3, "packet_loss_weight": 0.5, "download_speed_weight": 0.2}', '{"ipv4_count": null, "ipv6_count": 100000, "max_candidate": 500000, "FIRST_RUN_FLAG": false, "return_count_ips": 100, "tcping_semaphore_count": 20}', '{"count": 130, "auto_fill": true, "min_count": 15, "providers": [597], "auto_delete": true, "download_test_number": 5}', 'Default configuration');