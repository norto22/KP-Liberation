/*
    TIOW2 Imperial Guard BLUFOR Preset

    Needed Mods:
    - CBA_A3
    - Weapon Eventhandler Framework
    - There is Only War Mod - Release 5 BETA
    - TIOW2

    Notes:
    TIOW/TIOW2 classnames have changed across releases, so this preset discovers
    suitable TIOW classes from the loaded config and falls back to vanilla KP
    support assets where Liberation requires logistics/building objects.
*/

private _isTiowConfig = {
    params ["_cfg"];
    private _class = toLower configName _cfg;
    private _dlc = toLower getText (_cfg >> "DLC");
    private _addons = configSourceAddonList _cfg apply {toLower _x};
    private _hasTiowAddon = false;
    {if ((_x find "tiow") >= 0) exitWith {_hasTiowAddon = true};} forEach _addons;

    ((_class find "tiow") >= 0) ||
    {(_dlc find "tiow") >= 0} ||
    {_hasTiowAddon}
};

private _byName = {
    params ["_classes", "_terms"];

    _classes select {
        private _class = toLower _x;
        private _name = toLower getText (configFile >> "CfgVehicles" >> _x >> "displayName");
        private _matched = false;
        {
            if (((_class find _x) >= 0) || {(_name find _x) >= 0}) exitWith {_matched = true};
        } forEach _terms;
        _matched
    };
};

private _withFallback = {
    params ["_classes", "_fallback"];
    if (_classes isEqualTo []) exitWith {_fallback};
    _classes
};

private _priced = {
    params ["_classes", "_supplies", "_ammo", "_fuel", ["_limit", 12]];
    (_classes select [0, (_limit min count _classes)]) apply {[_x, _supplies, _ammo, _fuel]};
};

private _pick = {
    params ["_classes", "_terms", "_fallback"];
    private _matches = [_classes, _terms] call _byName;
    if (_matches isEqualTo []) exitWith {_fallback};
    _matches select 0
};

private _tiowVehicleConfigs = ("true" configClasses (configFile >> "CfgVehicles")) select {
    ((getNumber (_x >> "scope")) >= 2) && {[_x] call _isTiowConfig}
};

private _tiowVehicles = _tiowVehicleConfigs apply {configName _x};
private _westMen = (_tiowVehicleConfigs select {((getNumber (_x >> "side")) == 1) && {(configName _x) isKindOf "CAManBase"}}) apply {configName _x};
private _westVehicles = (_tiowVehicleConfigs select {((getNumber (_x >> "side")) == 1) && {!((configName _x) isKindOf "CAManBase")}}) apply {configName _x};

private _guardMen = [_westMen, ["cadian", "death korps", "krieg", "elysian", "guard", "guardsman", "kasrkin", "mechanicus", "skitarii"]] call _byName;
_guardMen = [_guardMen, ["B_Soldier_lite_F", "B_Soldier_F", "B_soldier_LAT_F", "B_Soldier_GL_F", "B_soldier_AR_F", "B_medic_F", "B_engineer_F", "B_soldier_AT_F", "B_soldier_AA_F"]] call _withFallback;

private _lightVehicles = [_westVehicles, ["taurox", "chimera", "centaur", "steg", "truck", "transport", "sentinel"]] call _byName;
private _heavyVehicles = [_westVehicles, ["leman", "russ", "malcador", "macharius", "baneblade", "crassus", "gorgon", "praetor", "tank"]] call _byName;
private _airVehicles = [_westVehicles, ["valkyrie", "vulture", "vendetta", "thunderbolt", "marauder", "arvus", "air"]] call _byName;
private _staticVehicles = [_westVehicles, ["heavy bolter", "lascannon", "autocannon", "mortar", "emplacement", "turret", "static"]] call _byName;
private _buildings = [_tiowVehicles, ["bunker", "bastion", "imperial", "fortification", "defence", "defense", "wall", "barricade"]] call _byName;

/*
    --- Support classnames ---
*/
FOB_typename = "Land_Cargo_HQ_V1_F";
FOB_box_typename = "B_Slingload_01_Cargo_F";
FOB_truck_typename = "B_Truck_01_box_F";
Arsenal_typename = "B_supplyCrate_F";
Respawn_truck_typename = "B_Truck_01_medical_F";
huron_typename = "B_Heli_Transport_03_unarmed_F";
crewman_classname = [_guardMen, ["crew", "tanker"], "B_crew_F"] call _pick;
pilot_classname = [_guardMen, ["pilot"], "B_Helipilot_F"] call _pick;
KPLIB_little_bird_classname = "B_Heli_Light_01_F";
KPLIB_boat_classname = "B_Boat_Transport_01_F";
KPLIB_truck_classname = "B_Truck_01_transport_F";
KPLIB_small_storage_building = "ContainmentArea_02_sand_F";
KPLIB_large_storage_building = "ContainmentArea_01_sand_F";
KPLIB_recycle_building = "Land_RepairDepot_01_tan_F";
KPLIB_air_vehicle_building = "B_Radar_System_01_F";
KPLIB_heli_slot_building = "Land_HelipadSquare_F";
KPLIB_plane_slot_building = "Land_TentHangar_V1_F";
KPLIB_supply_crate = "CargoNet_01_box_F";
KPLIB_ammo_crate = "B_CargoNet_01_ammo_F";
KPLIB_fuel_crate = "CargoNet_01_barrels_F";

infantry_units = [
    [[_guardMen, ["conscript", "light", "rifle"], "B_Soldier_lite_F"] call _pick, 15, 0, 0],
    [[_guardMen, ["rifleman", "guardsman"], "B_Soldier_F"] call _pick, 20, 0, 0],
    [[_guardMen, ["grenadier"], "B_Soldier_GL_F"] call _pick, 25, 0, 0],
    [[_guardMen, ["autorifle", "heavy stubber", "gunner"], "B_soldier_AR_F"] call _pick, 25, 0, 0],
    [[_guardMen, ["marksman", "sniper"], "B_soldier_M_F"] call _pick, 30, 0, 0],
    [[_guardMen, ["melta", "plasma", "missile", "anti tank", "at"], "B_soldier_LAT_F"] call _pick, 50, 10, 0],
    [[_guardMen, ["aa", "anti air"], "B_soldier_AA_F"] call _pick, 50, 10, 0],
    [[_guardMen, ["medic", "medicae"], "B_medic_F"] call _pick, 30, 0, 0],
    [[_guardMen, ["engineer", "sapper"], "B_engineer_F"] call _pick, 30, 0, 0],
    [[_guardMen, ["officer", "commander", "sergeant"], "B_Soldier_SL_F"] call _pick, 35, 0, 0],
    [[_guardMen, ["kasrkin", "veteran", "scion"], "B_Soldier_F"] call _pick, 40, 5, 0],
    [[_guardMen, ["elysian", "drop"], "B_soldier_PG_F"] call _pick, 25, 0, 0]
];

light_vehicles = [_lightVehicles, 125, 40, 75, 14] call _priced;
if (light_vehicles isEqualTo []) then {
    light_vehicles = [
        ["B_MRAP_01_F", 100, 0, 50],
        ["B_MRAP_01_hmg_F", 100, 40, 50],
        ["B_Truck_01_transport_F", 125, 0, 75],
        ["B_Truck_01_covered_F", 125, 0, 75]
    ];
};

heavy_vehicles = [_heavyVehicles, 400, 300, 200, 14] call _priced;
if (heavy_vehicles isEqualTo []) then {
    heavy_vehicles = [
        ["B_APC_Tracked_01_rcws_F", 300, 100, 150],
        ["B_MBT_01_cannon_F", 400, 300, 200],
        ["B_MBT_01_TUSK_F", 500, 350, 225]
    ];
};

air_vehicles = [_airVehicles, 500, 300, 250, 12] call _priced;
if (air_vehicles isEqualTo []) then {
    air_vehicles = [
        ["B_Heli_Transport_01_F", 250, 80, 150],
        ["B_Heli_Attack_01_dynamicLoadout_F", 500, 400, 200],
        ["B_Plane_CAS_01_dynamicLoadout_F", 1000, 800, 400]
    ];
};

static_vehicles = [_staticVehicles, 50, 80, 0, 12] call _priced;
if (static_vehicles isEqualTo []) then {
    static_vehicles = [
        ["B_HMG_01_F", 25, 40, 0],
        ["B_GMG_01_F", 35, 60, 0],
        ["B_static_AT_F", 50, 100, 0],
        ["B_Mortar_01_F", 80, 150, 0]
    ];
};

buildings = [
    ["Land_BagFence_Round_F", 5, 0, 0],
    ["Land_BagFence_Short_F", 5, 0, 0],
    ["Land_BagFence_Long_F", 10, 0, 0],
    ["Land_HBarrier_1_F", 10, 0, 0],
    ["Land_HBarrier_3_F", 15, 0, 0],
    ["Land_HBarrier_5_F", 20, 0, 0],
    ["Land_HBarrier_Big_F", 30, 0, 0],
    ["Land_Bunker_01_blocks_3_F", 40, 0, 0],
    ["Land_Bunker_01_small_F", 100, 0, 0]
];
buildings append ([_buildings, 60, 0, 0, 16] call _priced);

support_vehicles = [
    ["B_Truck_01_Repair_F", 325, 0, 75],
    ["B_Truck_01_ammo_F", 125, 200, 75],
    ["B_Truck_01_fuel_F", 125, 0, 275],
    ["B_Truck_01_medical_F", 100, 0, 50],
    ["B_APC_Tracked_01_CRV_F", 500, 250, 350]
];

blufor_squad_inf_light = _guardMen select [0, (4 min count _guardMen)];
blufor_squad_inf = _guardMen select [0, (8 min count _guardMen)];
blufor_squad_at = [
    [_guardMen, ["sergeant", "leader"], "B_Soldier_SL_F"] call _pick,
    [_guardMen, ["rifleman", "guardsman"], "B_Soldier_F"] call _pick,
    [_guardMen, ["melta", "missile", "anti tank", "at"], "B_soldier_LAT_F"] call _pick,
    [_guardMen, ["melta", "missile", "anti tank", "at"], "B_soldier_AT_F"] call _pick
];
blufor_squad_aa = [
    [_guardMen, ["sergeant", "leader"], "B_Soldier_SL_F"] call _pick,
    [_guardMen, ["rifleman", "guardsman"], "B_Soldier_F"] call _pick,
    [_guardMen, ["aa", "anti air"], "B_soldier_AA_F"] call _pick,
    [_guardMen, ["aa", "anti air"], "B_soldier_AA_F"] call _pick
];
blufor_squad_recon = _guardMen select [0, (6 min count _guardMen)];
blufor_squad_para = [_guardMen, ["elysian", "drop", "para"]] call _byName;
if (blufor_squad_para isEqualTo []) then {blufor_squad_para = blufor_squad_inf_light;};

elite_vehicles = (_heavyVehicles + _airVehicles) select [0, (8 min count (_heavyVehicles + _airVehicles))];
