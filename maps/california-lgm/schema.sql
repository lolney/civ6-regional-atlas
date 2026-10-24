CREATE TABLE "Map" (
		"ID" TEXT NOT NULL,
		"Width" INTEGER,
		"Height" INTEGER,
		"TopLatitude" INTEGER,
		"BottomLatitude" INTEGER,
		"WrapX" BOOLEAN,
		"WrapY" BOOLEAN,
		"MapSizeType" TEXT,
		PRIMARY KEY(ID));
CREATE TABLE "MapAttributes" (
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(Name));
CREATE TABLE "Plots" (
		"ID" INTEGER NOT NULL,
		"TerrainType" TEXT NOT NULL,
		"ContinentType" TEXT,
		"IsImpassable" BOOLEAN,
		PRIMARY KEY(ID));
CREATE TABLE "PlotAttributes" (
		"ID" INTEGER NOT NULL,
		"Type" TEXT NOT NULL,
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(ID, Type, Name));
CREATE TABLE "PlotRivers" (
		"ID" INTEGER NOT NULL,
		"IsNEOfRiver" BOOLEAN,
		"IsWOfRiver" BOOLEAN,
		"IsNWOfRiver" BOOLEAN,
		"EFlowDirection" INTEGER,
		"SEFlowDirection" INTEGER,
		"SWFlowDirection" INTEGER,
		PRIMARY KEY(ID));
CREATE TABLE "PlotCliffs" (
		"ID" INTEGER NOT NULL,
		"IsNEOfCliff" BOOLEAN,
		"IsWOfCliff" BOOLEAN,
		"IsNWOfCliff" BOOLEAN,
		PRIMARY KEY(ID));
CREATE TABLE "PlotResources" (
		"ID" INTEGER NOT NULL,
		"ResourceType" TEXT,
		"ResourceCount" INTEGER,
		PRIMARY KEY(ID));
CREATE TABLE "PlotFeatures" (
		"ID" INTEGER NOT NULL,
		"FeatureType" TEXT,
		PRIMARY KEY(ID));
CREATE TABLE "PlotImprovements" (
		"ID" INTEGER NOT NULL,
		"ImprovementType" TEXT,
		"ImprovementOwner" INTEGER,		-- The owner ID in the database, not the game
		PRIMARY KEY(ID));
CREATE TABLE "PlotRoutes" (
		"ID" INTEGER NOT NULL,
		"RouteType" TEXT,
		"RouteEra" TEXT,
		"IsRoutePillaged" BOOLEAN,
		PRIMARY KEY(ID));
CREATE TABLE "PlotOwners" (
		"ID" INTEGER NOT NULL,
		"Owner" INTEGER,				-- The owner ID in the database, not the game
		"CityOwner" INTEGER,			-- The city ID in the database, not the game
		"CityWorking" INTEGER,			-- The city ID in the database, not the game
		PRIMARY KEY(ID));
CREATE TABLE "RevealedPlots" (
		"ID" INTEGER NOT NULL,
		"Player" INTEGER,
		PRIMARY KEY(ID, Player));
CREATE TABLE "StartPositions" (
		"Plot" INTEGER NOT NULL,
		"Type" STRING NOT NULL,
		"Value" STRING NOT NULL,
		PRIMARY KEY("Plot"));
CREATE TABLE "Units" (
		"ID" INTEGER NOT NULL,
		"UnitType" TEXT NOT NULL,
		"Owner" INTEGER NOT NULL,		-- The owner ID in the database, not the game
		"Plot"	INTEGER NOT NULL,
		"Name"	TEXT,
		PRIMARY KEY(ID));
CREATE TABLE "UnitAttributes" (
		"ID" INTEGER NOT NULL,
		"Type" TEXT NOT NULL,
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(ID, Type, Name));
CREATE TABLE "Cities" (
		"Owner" INTEGER NOT NULL,		-- The owner ID in the database, not the game
		"Plot"	INTEGER NOT NULL,
		"Name"	TEXT,
		PRIMARY KEY(Plot));
CREATE TABLE "CityAttributes" (
		"ID" INTEGER NOT NULL,
		"Type" TEXT NOT NULL,
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(ID, Type, Name));
CREATE TABLE "Districts" (
		"DistrictType" TEXT NOT NULL,
		"CityID" INTEGER NOT NULL,		-- The city ID in the database, not the game
		"Plot"	INTEGER NOT NULL,
		PRIMARY KEY(Plot));
CREATE TABLE "DistrictAttributes" (
		"ID" INTEGER NOT NULL,
		"Type" TEXT NOT NULL,
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(ID, Type, Name));
CREATE TABLE "Buildings" (
		"BuildingType" TEXT NOT NULL,
		"Plot"	INTEGER NOT NULL,
		PRIMARY KEY(BuildingType, Plot));
CREATE TABLE "Players" (
		"ID" INTEGER NOT NULL,
		"CivilizationType" TEXT,
		"LeaderType" TEXT,
		"CivilizationLevelType" TEXT,
		"AgendaType" TEXT,
		"Status" TEXT,
		"Handicap" TEXT,
		"StartingPosition" TEXT,
		"Color" TEXT,
		"Initialized" BOOLEAN,
		PRIMARY KEY(ID));
CREATE TABLE "PlayerAttributes" (
		"ID" INTEGER NOT NULL,
		"Type" TEXT NOT NULL,
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(ID, Type, Name));
CREATE TABLE "ModComponents" (
		"Type" TEXT NOT NULL,
		"ID" TEXT NOT NULL,
		PRIMARY KEY(Type, ID));
CREATE TABLE "ModComponent_Properties" (
		"Type" TEXT NOT NULL,
		"ID" TEXT NOT NULL,
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(Type, ID, Name, Value));
CREATE TABLE "ModComponent_Items" (
		"Type" TEXT NOT NULL,
		"ID" TEXT NOT NULL,
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(Type, ID, Name, Value));
CREATE TABLE "ModSettings" (
		"Type" TEXT NOT NULL,
		"ID" TEXT NOT NULL,
		PRIMARY KEY(Type, ID));
CREATE TABLE "ModSettings_Items" (
		"Type" TEXT NOT NULL,
		"ID" TEXT NOT NULL,
		"Name" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(Type, ID, Name, Value));
CREATE TABLE "GameConfig" (
		"ID" TEXT NOT NULL,
		"Value" TEXT,
		PRIMARY KEY(ID));
CREATE TABLE "NamedRiverPlot" (
		"ID" INTEGER NOT NULL,
		"PlotIndex" INTEGER NOT NULL,
		"Edge" INTEGER NOT NULL,
		PRIMARY KEY(ID, PlotIndex, Edge));
CREATE TABLE "NamedRiver" (
		"ID" INTEGER NOT NULL,
		"Type" TEXT,
		"DiscoveringCiv" TEXT,
		"CustomName" TEXT,
		PRIMARY KEY(ID));
CREATE TABLE "MetaData" (
"Name" TEXT,
  "Value" TEXT
);
CREATE TABLE "ModProperties" (
"Name" TEXT,
  "Value" TEXT
);
CREATE TABLE "ModSettings_Properties" (
"Type" TEXT,
  "ID" TEXT,
  "Name" TEXT,
  "Value" TEXT
);
CREATE TABLE "ModText" (
"Language" TEXT,
  "ID" TEXT,
  "Value" TEXT
);
CREATE TABLE "ModDependencies" (
"ID" TEXT,
  "Title" TEXT
);