-- ============================================================
-- Bird Species Observation Analysis
-- Phase 2: Data Architecture — SSMS 22 DDL
-- Database: BirdObservationDB
-- Schema:   dbo
--
-- FIXES BAKED IN (no separate patch files needed):
--   [1] stg_bird_raw has exactly 43 columns matching the CSV
--       (Day_of_Week removed — never written by preprocessing notebook)
--   [2] BULK INSERT uses FORMAT='CSV' + FIELDQUOTE='"'
--       (handles Wind values with embedded commas e.g.
--        "Gentle breeze (8-12 mph), leaves in motion")
--   [3] ROWTERMINATOR = '0x0a'  (pandas LF line endings)
--   [4] PATH placeholder clearly marked — update before running
-- ============================================================

-- ============================================================
-- 1. Create Database
-- ============================================================
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'BirdObservationDB')
    CREATE DATABASE BirdObservationDB;
GO

USE BirdObservationDB;
GO

-- ============================================================
-- 2. Dimension Tables
-- ============================================================

IF OBJECT_ID('dbo.dim_admin_unit','U') IS NOT NULL DROP TABLE dbo.dim_admin_unit;
CREATE TABLE dbo.dim_admin_unit (
    Admin_Unit_Code  NVARCHAR(10)  NOT NULL PRIMARY KEY,
    Admin_Unit_Name  NVARCHAR(100) NULL,
    Region           NVARCHAR(50)  NULL
);
GO

IF OBJECT_ID('dbo.dim_species','U') IS NOT NULL DROP TABLE dbo.dim_species;
CREATE TABLE dbo.dim_species (
    AOU_Code                    NVARCHAR(10)  NOT NULL PRIMARY KEY,
    Common_Name                 NVARCHAR(150) NOT NULL,
    Scientific_Name             NVARCHAR(200) NOT NULL,
    AcceptedTSN                 BIGINT        NULL,
    TaxonCode                   BIGINT        NULL,
    PIF_Watchlist_Status        BIT           NOT NULL DEFAULT 0,
    Regional_Stewardship_Status BIT           NOT NULL DEFAULT 0
);
GO

IF OBJECT_ID('dbo.dim_plot','U') IS NOT NULL DROP TABLE dbo.dim_plot;
CREATE TABLE dbo.dim_plot (
    Plot_Name       NVARCHAR(20)  NOT NULL PRIMARY KEY,
    Site_Name       NVARCHAR(100) NULL,
    Admin_Unit_Code NVARCHAR(10)  NOT NULL,
    Sub_Unit_Code   NVARCHAR(20)  NULL,
    Location_Type   NVARCHAR(30)  NOT NULL
);
GO

IF OBJECT_ID('dbo.dim_observer','U') IS NOT NULL DROP TABLE dbo.dim_observer;
CREATE TABLE dbo.dim_observer (
    Observer_ID   INT IDENTITY(1,1) PRIMARY KEY,
    Observer_Name NVARCHAR(150) NOT NULL UNIQUE
);
GO

IF OBJECT_ID('dbo.dim_date','U') IS NOT NULL DROP TABLE dbo.dim_date;
CREATE TABLE dbo.dim_date (
    Date_Key    INT          NOT NULL PRIMARY KEY,
    Date_Value  DATE         NOT NULL,
    Year        SMALLINT     NOT NULL,
    Month       TINYINT      NOT NULL,
    Month_Name  NVARCHAR(10) NOT NULL,
    Quarter     TINYINT      NOT NULL,
    Season      NVARCHAR(10) NOT NULL,
    Day_of_Week NVARCHAR(10) NOT NULL
);
GO

-- ============================================================
-- 3. Fact Table
-- ============================================================

IF OBJECT_ID('dbo.fact_observations','U') IS NOT NULL DROP TABLE dbo.fact_observations;
CREATE TABLE dbo.fact_observations (
    Observation_ID          BIGINT IDENTITY(1,1) PRIMARY KEY,
    -- Keys
    Admin_Unit_Code         NVARCHAR(10)  NOT NULL,
    Plot_Name               NVARCHAR(20)  NOT NULL,
    Date_Key                INT           NOT NULL,
    Observer_ID             INT           NOT NULL,
    AOU_Code                NVARCHAR(10)  NOT NULL,
    -- Context
    Habitat_Source          NVARCHAR(20)  NOT NULL,
    Year                    SMALLINT      NOT NULL,
    Visit                   TINYINT       NULL,
    Interval_Length         NVARCHAR(20)  NULL,
    Interval_Mid_Min        DECIMAL(5,2)  NULL,
    ID_Method               NVARCHAR(30)  NULL,
    Start_Time              TIME          NULL,
    End_Time                TIME          NULL,
    Start_Hour              TINYINT       NULL,
    Season                  NVARCHAR(10)  NULL,
    -- Metrics
    Distance                NVARCHAR(30)  NULL,
    Distance_Rank           TINYINT       NULL,
    Flyover_Observed        BIT           NULL,
    Sex                     NVARCHAR(20)  NULL,
    Previously_Obs          BIT           NULL,
    Initial_Three_Min_Cnt   BIT           NULL,
    -- Environment
    Temperature             DECIMAL(5,1)  NULL,
    Humidity                DECIMAL(5,1)  NULL,
    Sky                     NVARCHAR(50)  NULL,
    Sky_Clean               NVARCHAR(30)  NULL,
    Wind                    NVARCHAR(100) NULL,
    Wind_Category           NVARCHAR(20)  NULL,
    Disturbance             NVARCHAR(100) NULL,
    Disturbance_Level       NVARCHAR(20)  NULL,
    -- Conservation
    At_Risk                 BIT           NOT NULL DEFAULT 0,
    -- Audit
    Loaded_At               DATETIME2     NOT NULL DEFAULT SYSDATETIME(),
    Source_Sheet            NVARCHAR(10)  NULL
);
GO

-- ============================================================
-- 4. Indexes
-- ============================================================

CREATE NONCLUSTERED INDEX ix_fact_admin_unit ON dbo.fact_observations (Admin_Unit_Code);
CREATE NONCLUSTERED INDEX ix_fact_date       ON dbo.fact_observations (Date_Key);
CREATE NONCLUSTERED INDEX ix_fact_species    ON dbo.fact_observations (AOU_Code);
CREATE NONCLUSTERED INDEX ix_fact_habitat    ON dbo.fact_observations (Habitat_Source, Year, Admin_Unit_Code);
CREATE NONCLUSTERED INDEX ix_fact_atrisk     ON dbo.fact_observations (At_Risk, Admin_Unit_Code);
GO

-- ============================================================
-- 5. Seed dim_admin_unit
-- ============================================================

INSERT INTO dbo.dim_admin_unit (Admin_Unit_Code, Admin_Unit_Name, Region) VALUES
    ('ANTI', 'Antietam National Battlefield',                    'National Capital Region'),
    ('CATO', 'Catoctin Mountain Park',                           'National Capital Region'),
    ('CHOH', 'Chesapeake & Ohio Canal National Historic Park',   'National Capital Region'),
    ('GWMP', 'George Washington Memorial Parkway',               'National Capital Region'),
    ('HAFE', 'Harpers Ferry National Historical Park',           'National Capital Region'),
    ('MANA', 'Manassas National Battlefield Park',               'National Capital Region'),
    ('MONO', 'Monocacy National Battlefield',                    'National Capital Region'),
    ('NACE', 'National Capital Parks-East',                      'National Capital Region'),
    ('PRWI', 'Prince William Forest Park',                       'National Capital Region'),
    ('ROCR', 'Rock Creek Park',                                  'National Capital Region'),
    ('WOTR', 'Wolf Trap National Park for the Performing Arts',  'National Capital Region');
GO

-- ============================================================
-- 6. Seed dim_date (2015-2030)
-- ============================================================

DECLARE @d DATE = '2015-01-01';
WHILE @d <= '2030-12-31'
BEGIN
    INSERT INTO dbo.dim_date
        (Date_Key, Date_Value, Year, Month, Month_Name, Quarter, Season, Day_of_Week)
    VALUES (
        CAST(FORMAT(@d,'yyyyMMdd') AS INT), @d,
        YEAR(@d), MONTH(@d), DATENAME(MONTH,@d), DATEPART(QUARTER,@d),
        CASE WHEN MONTH(@d) IN (3,4,5)   THEN 'Spring'
             WHEN MONTH(@d) IN (6,7,8)   THEN 'Summer'
             WHEN MONTH(@d) IN (9,10,11) THEN 'Autumn'
             ELSE 'Winter' END,
        DATENAME(WEEKDAY,@d)
    );
    SET @d = DATEADD(DAY,1,@d);
END;
GO

-- ============================================================
-- 7. Analytical Views
-- ============================================================

CREATE OR ALTER VIEW dbo.vw_diversity_by_unit AS
SELECT f.Admin_Unit_Code, f.Habitat_Source, f.Year,
    COUNT(*)                                        AS Total_Observations,
    COUNT(DISTINCT f.AOU_Code)                      AS Unique_Species,
    SUM(CAST(f.At_Risk AS INT))                     AS AtRisk_Observations,
    COUNT(DISTINCT CASE WHEN f.At_Risk=1 THEN f.AOU_Code END) AS AtRisk_Species,
    AVG(f.Temperature)                              AS Avg_Temperature,
    AVG(f.Humidity)                                 AS Avg_Humidity
FROM dbo.fact_observations f
GROUP BY f.Admin_Unit_Code, f.Habitat_Source, f.Year;
GO

CREATE OR ALTER VIEW dbo.vw_temporal_heatmap AS
SELECT f.Year, d.Month, d.Month_Name, d.Season,
    f.Admin_Unit_Code, f.Habitat_Source,
    COUNT(*)                   AS Observations,
    COUNT(DISTINCT f.AOU_Code) AS Unique_Species
FROM dbo.fact_observations f
JOIN dbo.dim_date d ON f.Date_Key = d.Date_Key
GROUP BY f.Year, d.Month, d.Month_Name, d.Season, f.Admin_Unit_Code, f.Habitat_Source;
GO

CREATE OR ALTER VIEW dbo.vw_top_species AS
SELECT f.Admin_Unit_Code, f.Habitat_Source,
    s.Common_Name, s.Scientific_Name, s.AOU_Code,
    s.PIF_Watchlist_Status, s.Regional_Stewardship_Status,
    COUNT(*)                   AS Observations,
    COUNT(DISTINCT f.Date_Key) AS Survey_Days
FROM dbo.fact_observations f
JOIN dbo.dim_species s ON f.AOU_Code = s.AOU_Code
GROUP BY f.Admin_Unit_Code, f.Habitat_Source, s.Common_Name, s.Scientific_Name,
         s.AOU_Code, s.PIF_Watchlist_Status, s.Regional_Stewardship_Status;
GO

CREATE OR ALTER VIEW dbo.vw_environmental_impact AS
SELECT f.Admin_Unit_Code, f.Habitat_Source,
    f.Sky_Clean, f.Wind_Category, f.Disturbance_Level,
    ROUND(CAST(f.Temperature AS FLOAT),0) AS Temp_Rounded,
    COUNT(*)                   AS Observations,
    COUNT(DISTINCT f.AOU_Code) AS Unique_Species
FROM dbo.fact_observations f
GROUP BY f.Admin_Unit_Code, f.Habitat_Source, f.Sky_Clean,
         f.Wind_Category, f.Disturbance_Level,
         ROUND(CAST(f.Temperature AS FLOAT),0);
GO

-- ============================================================
-- 8. Staging Table — exact 43 columns matching the CSV
-- ============================================================
-- Column order matches bird_observations_clean.csv exactly.
-- Every column is NVARCHAR(500) to accept raw CSV values
-- including pandas True/False strings and quoted Wind fields.

IF OBJECT_ID('dbo.stg_bird_raw','U') IS NOT NULL DROP TABLE dbo.stg_bird_raw;
CREATE TABLE dbo.stg_bird_raw (
    --  #   CSV column
    --  1   Admin_Unit_Code
    Admin_Unit_Code             NVARCHAR(500),
    --  2   Sub_Unit_Code
    Sub_Unit_Code               NVARCHAR(500),
    --  3   Site_Name
    Site_Name                   NVARCHAR(500),
    --  4   Plot_Name
    Plot_Name                   NVARCHAR(500),
    --  5   Location_Type
    Location_Type               NVARCHAR(500),
    --  6   Year
    Year                        NVARCHAR(500),
    --  7   Date
    Date                        NVARCHAR(500),
    --  8   Start_Time
    Start_Time                  NVARCHAR(500),
    --  9   End_Time
    End_Time                    NVARCHAR(500),
    -- 10   Observer
    Observer                    NVARCHAR(500),
    -- 11   Visit
    Visit                       NVARCHAR(500),
    -- 12   Interval_Length
    Interval_Length             NVARCHAR(500),
    -- 13   ID_Method
    ID_Method                   NVARCHAR(500),
    -- 14   Distance
    Distance                    NVARCHAR(500),
    -- 15   Flyover_Observed
    Flyover_Observed            NVARCHAR(500),
    -- 16   Sex
    Sex                         NVARCHAR(500),
    -- 17   Common_Name
    Common_Name                 NVARCHAR(500),
    -- 18   Scientific_Name
    Scientific_Name             NVARCHAR(500),
    -- 19   AcceptedTSN
    AcceptedTSN                 NVARCHAR(500),
    -- 20   TaxonCode
    TaxonCode                   NVARCHAR(500),
    -- 21   AOU_Code
    AOU_Code                    NVARCHAR(500),
    -- 22   PIF_Watchlist_Status
    PIF_Watchlist_Status        NVARCHAR(500),
    -- 23   Regional_Stewardship_Status
    Regional_Stewardship_Status NVARCHAR(500),
    -- 24   Temperature
    Temperature                 NVARCHAR(500),
    -- 25   Humidity
    Humidity                    NVARCHAR(500),
    -- 26   Sky
    Sky                         NVARCHAR(500),
    -- 27   Wind  <-- quoted in CSV when it contains a comma
    Wind                        NVARCHAR(500),
    -- 28   Disturbance
    Disturbance                 NVARCHAR(500),
    -- 29   Previously_Obs
    Previously_Obs              NVARCHAR(500),
    -- 30   Initial_Three_Min_Cnt
    Initial_Three_Min_Cnt       NVARCHAR(500),
    -- 31   Habitat_Source
    Habitat_Source              NVARCHAR(500),
    -- 32   Source_Sheet
    Source_Sheet                NVARCHAR(500),
    -- 33   Month
    Month                       NVARCHAR(500),
    -- 34   Month_Name
    Month_Name                  NVARCHAR(500),
    -- 35   Season
    Season                      NVARCHAR(500),
    -- 36   Start_Hour
    Start_Hour                  NVARCHAR(500),
    -- 37   Distance_Clean
    Distance_Clean              NVARCHAR(500),
    -- 38   Distance_Rank
    Distance_Rank               NVARCHAR(500),
    -- 39   Sky_Clean
    Sky_Clean                   NVARCHAR(500),
    -- 40   Wind_Category
    Wind_Category               NVARCHAR(500),
    -- 41   Disturbance_Level
    Disturbance_Level           NVARCHAR(500),
    -- 42   At_Risk
    At_Risk                     NVARCHAR(500),
    -- 43   Interval_Mid_Min
    Interval_Mid_Min            NVARCHAR(500)
    -- Total: 43 columns — matches CSV exactly
);
GO

-- Verify column count before BULK INSERT
SELECT COUNT(*) AS Staging_Column_Count        -- must be 43
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'stg_bird_raw';
GO

-- ============================================================
-- 9. BULK INSERT
-- ============================================================
-- UPDATE the path below to where your CSV is saved.
-- The SQL Server service account must have READ access to that folder.
-- If OneDrive sync causes access errors, copy the CSV to C:\BirdData\
--
-- Common paths:
--   C:\BirdData\bird_observations_clean.csv
--   C:\Users\richa\Desktop\bird_analysis_project\bird_analysis\dashboard\bird_observations_clean.csv

BULK INSERT dbo.stg_bird_raw
FROM 'C:\BirdData\bird_observations_clean.csv'      -- <<< UPDATE THIS PATH
WITH (
    FORMAT          = 'CSV',      -- RFC 4180: quoted fields with commas are atomic
    FIELDQUOTE      = '"',        -- handles Wind: "Gentle breeze (8-12 mph), leaves in motion"
    FIRSTROW        = 2,          -- skip header row
    FIELDTERMINATOR = ',',
    ROWTERMINATOR   = '0x0a',     -- LF (pandas default); change to '0x0d0a' if CRLF
    CODEPAGE        = '65001',    -- UTF-8
    TABLOCK,
    KEEPNULLS
);
GO

-- Verify: should be ~17,077
SELECT COUNT(*) AS Staging_Row_Count FROM dbo.stg_bird_raw;

-- Spot-check quoted Wind value loaded correctly
SELECT TOP 3 Wind, Wind_Category
FROM dbo.stg_bird_raw
WHERE Wind LIKE '%leaves in motion%';
GO

-- ============================================================
-- 10. Load dim_species
-- ============================================================

INSERT INTO dbo.dim_species (
    AOU_Code, Common_Name, Scientific_Name,
    AcceptedTSN, TaxonCode,
    PIF_Watchlist_Status, Regional_Stewardship_Status
)
SELECT
    LTRIM(RTRIM(AOU_Code)),
    LTRIM(RTRIM(Common_Name)),
    LTRIM(RTRIM(Scientific_Name)),
    TRY_CAST(NULLIF(LTRIM(RTRIM(AcceptedTSN)),'') AS BIGINT),
    TRY_CAST(NULLIF(LTRIM(RTRIM(TaxonCode)),  '') AS BIGINT),
    CASE WHEN LTRIM(RTRIM(PIF_Watchlist_Status))        = 'True' THEN 1 ELSE 0 END,
    CASE WHEN LTRIM(RTRIM(Regional_Stewardship_Status)) = 'True' THEN 1 ELSE 0 END
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY LTRIM(RTRIM(AOU_Code)) ORDER BY (SELECT NULL)) AS rn
    FROM dbo.stg_bird_raw
    WHERE NULLIF(LTRIM(RTRIM(AOU_Code)),        '') IS NOT NULL
      AND NULLIF(LTRIM(RTRIM(Common_Name)),     '') IS NOT NULL
      AND NULLIF(LTRIM(RTRIM(Scientific_Name)), '') IS NOT NULL
) d WHERE rn = 1;

SELECT COUNT(*) AS dim_species_loaded FROM dbo.dim_species;   -- expected ~127
GO

-- ============================================================
-- 11. Load dim_plot
-- ============================================================

INSERT INTO dbo.dim_plot (Plot_Name, Site_Name, Admin_Unit_Code, Sub_Unit_Code, Location_Type)
SELECT
    LTRIM(RTRIM(Plot_Name)),
    NULLIF(LTRIM(RTRIM(Site_Name)),     ''),
    LTRIM(RTRIM(Admin_Unit_Code)),
    NULLIF(LTRIM(RTRIM(Sub_Unit_Code)), ''),
    LTRIM(RTRIM(Location_Type))
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY LTRIM(RTRIM(Plot_Name)) ORDER BY (SELECT NULL)) AS rn
    FROM dbo.stg_bird_raw
    WHERE NULLIF(LTRIM(RTRIM(Plot_Name)),    '') IS NOT NULL
      AND NULLIF(LTRIM(RTRIM(Location_Type)),'') IS NOT NULL
) d WHERE rn = 1;

SELECT COUNT(*) AS dim_plot_loaded FROM dbo.dim_plot;
GO

-- ============================================================
-- 12. Load dim_observer
-- ============================================================

INSERT INTO dbo.dim_observer (Observer_Name)
SELECT DISTINCT LTRIM(RTRIM(Observer))
FROM dbo.stg_bird_raw
WHERE NULLIF(LTRIM(RTRIM(Observer)),'') IS NOT NULL;

SELECT COUNT(*) AS dim_observer_loaded FROM dbo.dim_observer;  -- expected 4
GO

-- ============================================================
-- 13. Load fact_observations
-- ============================================================

INSERT INTO dbo.fact_observations (
    Admin_Unit_Code, Plot_Name, Date_Key, Observer_ID, AOU_Code,
    Habitat_Source, Year, Visit, Interval_Length, Interval_Mid_Min,
    ID_Method, Start_Time, End_Time, Start_Hour, Season,
    Distance, Distance_Rank, Flyover_Observed, Sex,
    Previously_Obs, Initial_Three_Min_Cnt,
    Temperature, Humidity, Sky, Sky_Clean,
    Wind, Wind_Category, Disturbance, Disturbance_Level,
    At_Risk, Source_Sheet
)
SELECT
    LTRIM(RTRIM(s.Admin_Unit_Code)),
    LTRIM(RTRIM(s.Plot_Name)),
    CAST(FORMAT(TRY_CAST(LEFT(LTRIM(RTRIM(s.Date)),10) AS DATE),'yyyyMMdd') AS INT),
    o.Observer_ID,
    LTRIM(RTRIM(s.AOU_Code)),
    LTRIM(RTRIM(s.Habitat_Source)),
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.Year)),  '') AS SMALLINT),
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.Visit)), '') AS TINYINT),
    NULLIF(LTRIM(RTRIM(s.Interval_Length)),''),
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.Interval_Mid_Min)),'') AS DECIMAL(5,2)),
    NULLIF(LTRIM(RTRIM(s.ID_Method)),''),
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.Start_Time)),'') AS TIME),
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.End_Time)),  '') AS TIME),
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.Start_Hour)),'') AS TINYINT),
    NULLIF(LTRIM(RTRIM(s.Season)),''),
    NULLIF(LTRIM(RTRIM(s.Distance)),''),
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.Distance_Rank)),'') AS TINYINT),
    CASE WHEN LTRIM(RTRIM(s.Flyover_Observed))      ='True'  THEN 1
         WHEN LTRIM(RTRIM(s.Flyover_Observed))      ='False' THEN 0 ELSE NULL END,
    NULLIF(LTRIM(RTRIM(s.Sex)),''),
    CASE WHEN LTRIM(RTRIM(s.Previously_Obs))        ='True'  THEN 1
         WHEN LTRIM(RTRIM(s.Previously_Obs))        ='False' THEN 0 ELSE NULL END,
    CASE WHEN LTRIM(RTRIM(s.Initial_Three_Min_Cnt)) ='True'  THEN 1
         WHEN LTRIM(RTRIM(s.Initial_Three_Min_Cnt)) ='False' THEN 0 ELSE NULL END,
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.Temperature)),'') AS DECIMAL(5,1)),
    TRY_CAST(NULLIF(LTRIM(RTRIM(s.Humidity)),   '') AS DECIMAL(5,1)),
    NULLIF(LTRIM(RTRIM(s.Sky)),''),
    NULLIF(LTRIM(RTRIM(s.Sky_Clean)),''),
    NULLIF(LTRIM(RTRIM(s.Wind)),''),
    NULLIF(LTRIM(RTRIM(s.Wind_Category)),''),
    NULLIF(LTRIM(RTRIM(s.Disturbance)),''),
    NULLIF(LTRIM(RTRIM(s.Disturbance_Level)),''),
    CASE WHEN LTRIM(RTRIM(s.At_Risk)) = 'True' THEN 1 ELSE 0 END,
    NULLIF(LTRIM(RTRIM(s.Source_Sheet)),'')
FROM dbo.stg_bird_raw s
INNER JOIN dbo.dim_observer o ON LTRIM(RTRIM(s.Observer)) = o.Observer_Name
WHERE
    NULLIF(LTRIM(RTRIM(s.Admin_Unit_Code)),  '') IS NOT NULL
    AND NULLIF(LTRIM(RTRIM(s.Plot_Name)),    '') IS NOT NULL
    AND NULLIF(LTRIM(RTRIM(s.AOU_Code)),     '') IS NOT NULL
    AND NULLIF(LTRIM(RTRIM(s.Observer)),     '') IS NOT NULL
    AND NULLIF(LTRIM(RTRIM(s.Date)),         '') IS NOT NULL
    AND NULLIF(LTRIM(RTRIM(s.Habitat_Source)),'') IS NOT NULL
    AND NULLIF(LTRIM(RTRIM(s.Year)),         '') IS NOT NULL
    AND TRY_CAST(LEFT(LTRIM(RTRIM(s.Date)),10) AS DATE) IS NOT NULL;

SELECT COUNT(*) AS fact_loaded FROM dbo.fact_observations;  -- expected ~17,077
GO

-- ============================================================
-- 14. Row Count Summary
-- ============================================================

SELECT 'stg_bird_raw'      AS [Table], COUNT(*) AS [Rows] FROM dbo.stg_bird_raw
UNION ALL SELECT 'dim_species',         COUNT(*)           FROM dbo.dim_species
UNION ALL SELECT 'dim_plot',            COUNT(*)           FROM dbo.dim_plot
UNION ALL SELECT 'dim_observer',        COUNT(*)           FROM dbo.dim_observer
UNION ALL SELECT 'dim_admin_unit',      COUNT(*)           FROM dbo.dim_admin_unit
UNION ALL SELECT 'fact_observations',   COUNT(*)           FROM dbo.fact_observations;
GO
-- Expected:
--   stg_bird_raw      ~17,077
--   dim_species       ~127
--   dim_plot          ~200+
--   dim_observer      4
--   dim_admin_unit    11
--   fact_observations ~17,077

-- ============================================================
-- 15. Referential Integrity Checks (all must return 0)
-- ============================================================

SELECT COUNT(*) AS Orphaned_AOU  FROM dbo.fact_observations f
WHERE NOT EXISTS (SELECT 1 FROM dbo.dim_species s WHERE s.AOU_Code  = f.AOU_Code);

SELECT COUNT(*) AS Orphaned_Plot FROM dbo.fact_observations f
WHERE NOT EXISTS (SELECT 1 FROM dbo.dim_plot   p WHERE p.Plot_Name  = f.Plot_Name);

SELECT COUNT(*) AS Orphaned_Date FROM dbo.fact_observations f
WHERE NOT EXISTS (SELECT 1 FROM dbo.dim_date   d WHERE d.Date_Key   = f.Date_Key);
GO

-- ============================================================
-- 16. Smoke Test via Views
-- ============================================================

SELECT TOP 10
    Admin_Unit_Code, Habitat_Source, Year,
    Total_Observations, Unique_Species, AtRisk_Species,
    CAST(Avg_Temperature AS DECIMAL(5,1)) AS Avg_Temp_C
FROM dbo.vw_diversity_by_unit
ORDER BY Unique_Species DESC;
GO

-- ============================================================
-- 17. Drop staging once all counts look correct
-- ============================================================
-- Uncomment and run when you are satisfied with the load.

-- DROP TABLE dbo.stg_bird_raw;
-- GO
