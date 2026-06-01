/*
    TIOW2 Ork OPFOR Preset

    Needed Mods:
    - CBA_A3
    - Weapon Eventhandler Framework
    - There is Only War Mod - Release 5 BETA
    - TIOW2
*/

private _isTiowConfig = {
    params ["_cfg"];
    private _class = toLower configName _cfg;
    private _dlc = toLower getText (_cfg >> "DLC");
    private _addons = configSourceAddonList _cfg apply {toLower _x};
    private _has40kAddon = false;
    {
        if (((_x find "tiow") >= 0) || {(_x find "ork") >= 0} || {(_x find "40k") >= 0} || {(_x find "wh") >= 0}) exitWith {
            _has40kAddon = true;
        };
    } forEach _addons;

    ((_class find "tiow") >= 0) ||
    {(_class find "ork") >= 0} ||
    {(_class find "gretchin") >= 0} ||
    {(_class find "stormboy") >= 0} ||
    {(_class find "shoota") >= 0} ||
    {(_dlc find "tiow") >= 0} ||
    {_has40kAddon}
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

private _pick = {
    params ["_classes", "_terms", "_fallback"];
    private _matches = [_classes, _terms] call _byName;
    if (_matches isEqualTo []) exitWith {_fallback};
    _matches select 0
};

private _tiowVehicleConfigs = ("true" configClasses (configFile >> "CfgVehicles")) select {
    ((getNumber (_x >> "scope")) >= 2) && {[_x] call _isTiowConfig}
};

private _eastMen = (_tiowVehicleConfigs select {((getNumber (_x >> "side")) == 0) && {(configName _x) isKindOf "CAManBase"}}) apply {configName _x};
private _eastVehicles = (_tiowVehicleConfigs select {((getNumber (_x >> "side")) == 0) && {!((configName _x) isKindOf "CAManBase")}}) apply {configName _x};

private _orkMen = [_eastMen, ["ork", "gretchin", "stormboy", "nob", "boy", "shoota", "slugga", "mek", "painboy"]] call _byName;
private _enemyMen = (_orkMen + _eastMen) arrayIntersect (_orkMen + _eastMen);
_enemyMen = [_enemyMen, ["O_Soldier_lite_F", "O_Soldier_F", "O_Soldier_LAT_F", "O_Soldier_GL_F", "O_Soldier_AR_F", "O_medic_F", "O_engineer_F", "O_Soldier_AT_F", "O_Soldier_AA_F"]] call _withFallback;

private _orkVehicles = [_eastVehicles, ["ork", "trukk", "truck", "battlewagon", "stompa", "looted", "deff", "kopta", "buggy", "warbike", "dakka", "big gun"]] call _byName;
private _lightVehicles = [_orkVehicles, ["trukk", "truck", "technical", "transport", "buggy", "warbike", "bike"]] call _byName;
private _armorVehicles = [_orkVehicles, ["battlewagon", "stompa", "looted", "tank", "wagon", "armor", "armour"]] call _byName;
private _airVehicles = [_orkVehicles, ["deffkopta", "kopta", "air", "plane", "fighta"]] call _byName;
private _staticVehicles = [_orkVehicles, ["dakka", "big gun", "mortar", "emplacement", "turret", "static"]] call _byName;

// Enemy infantry classes
opfor_officer = [_enemyMen, ["officer", "commander", "boss", "nob"], "O_officer_F"] call _pick;
opfor_squad_leader = [_enemyMen, ["leader", "sergeant", "enforcer", "boss", "nob"], "O_Soldier_SL_F"] call _pick;
opfor_team_leader = [_enemyMen, ["leader", "sergeant", "enforcer", "boss", "nob"], "O_Soldier_TL_F"] call _pick;
opfor_sentry = [_enemyMen, ["militia", "cultist", "gretchin", "light"], "O_Soldier_lite_F"] call _pick;
opfor_rifleman = [_enemyMen, ["ork", "boy", "shoota", "slugga"], "O_Soldier_F"] call _pick;
opfor_rpg = [_enemyMen, ["rokkit", "rocket", "rpg", "missile", "anti tank", "at"], "O_Soldier_LAT_F"] call _pick;
opfor_grenadier = [_enemyMen, ["grenadier", "grenade"], "O_Soldier_GL_F"] call _pick;
opfor_machinegunner = [_enemyMen, ["big shoota", "shoota", "dakka", "gunner", "autorifle"], "O_Soldier_AR_F"] call _pick;
opfor_heavygunner = [_enemyMen, ["heavy", "big shoota", "dakka", "autocannon"], "O_HeavyGunner_F"] call _pick;
opfor_marksman = [_enemyMen, ["marksman", "sniper"], "O_soldier_M_F"] call _pick;
opfor_sharpshooter = [_enemyMen, ["sharpshooter", "sniper"], "O_Sharpshooter_F"] call _pick;
opfor_sniper = [_enemyMen, ["sniper"], "O_sniper_F"] call _pick;
opfor_at = [_enemyMen, ["melta", "rokkit", "missile", "anti tank", "at"], "O_Soldier_AT_F"] call _pick;
opfor_aa = [_enemyMen, ["aa", "anti air"], "O_Soldier_AA_F"] call _pick;
opfor_medic = [_enemyMen, ["medic", "medicae", "painboy"], "O_medic_F"] call _pick;
opfor_engineer = [_enemyMen, ["engineer", "sapper", "mek"], "O_engineer_F"] call _pick;
opfor_paratrooper = [_enemyMen, ["stormboy", "jump", "drop"], "O_soldier_PG_F"] call _pick;

// Enemy vehicles used by secondary objectives.
opfor_mrap = if (_lightVehicles isEqualTo []) then {"O_MRAP_02_F"} else {_lightVehicles select 0};
opfor_mrap_armed = if (_lightVehicles isEqualTo []) then {
    "O_MRAP_02_hmg_F"
} else {
    private _armedVehicle = _lightVehicles select 0;
    {if (((toLower _x) find "armed") >= 0) exitWith {_armedVehicle = _x};} forEach _lightVehicles;
    _armedVehicle
};
opfor_transport_helo = if (_airVehicles isEqualTo []) then {"O_Heli_Transport_04_bench_F"} else {_airVehicles select 0};
opfor_transport_truck = if (_lightVehicles isEqualTo []) then {"O_Truck_03_covered_F"} else {_lightVehicles select 0};
opfor_ammobox_transport = "O_Truck_03_transport_F";
opfor_fuel_truck = "O_Truck_03_fuel_F";
opfor_ammo_truck = "O_Truck_03_ammo_F";
opfor_fuel_container = "Land_Pod_Heli_Transport_04_fuel_F";
opfor_ammo_container = "Land_Pod_Heli_Transport_04_ammo_F";
opfor_flag = "Flag_CSAT_F";

militia_squad = [
    opfor_sentry,
    opfor_sentry,
    opfor_rifleman,
    opfor_rifleman,
    opfor_rpg,
    opfor_machinegunner,
    opfor_marksman,
    opfor_medic,
    opfor_engineer
];

militia_vehicles = _lightVehicles select [0, (4 min count _lightVehicles)];
if (militia_vehicles isEqualTo []) then {militia_vehicles = ["O_LSV_02_armed_F"];};

opfor_vehicles = (_lightVehicles + _armorVehicles + _staticVehicles) select [0, (18 min count (_lightVehicles + _armorVehicles + _staticVehicles))];
if (opfor_vehicles isEqualTo []) then {
    opfor_vehicles = [
        "O_MRAP_02_hmg_F",
        "O_MRAP_02_gmg_F",
        "O_LSV_02_AT_F",
        "O_APC_Tracked_02_cannon_F",
        "O_APC_Tracked_02_AA_F",
        "O_MBT_02_cannon_F"
    ];
};

opfor_vehicles_low_intensity = (_lightVehicles + militia_vehicles) select [0, (8 min count (_lightVehicles + militia_vehicles))];
if (opfor_vehicles_low_intensity isEqualTo []) then {
    opfor_vehicles_low_intensity = [
        "O_MRAP_02_hmg_F",
        "O_LSV_02_AT_F",
        "O_APC_Wheeled_02_rcws_F"
    ];
};

opfor_battlegroup_vehicles = (opfor_vehicles + _airVehicles) select [0, (24 min count (opfor_vehicles + _airVehicles))];
opfor_battlegroup_vehicles_low_intensity = (opfor_vehicles_low_intensity + (_airVehicles select [0, (2 min count _airVehicles)])) select [0, 12];
opfor_troup_transports = (_lightVehicles + _armorVehicles + _airVehicles) select [0, (10 min count (_lightVehicles + _armorVehicles + _airVehicles))];
if (opfor_troup_transports isEqualTo []) then {
    opfor_troup_transports = [
        "O_Truck_03_transport_F",
        "O_Truck_03_covered_F",
        "O_APC_Wheeled_02_rcws_F",
        "O_Heli_Transport_04_bench_F"
    ];
};

opfor_choppers = _airVehicles select [0, (6 min count _airVehicles)];
if (opfor_choppers isEqualTo []) then {
    opfor_choppers = [
        "O_Heli_Light_02_dynamicLoadout_F",
        "O_Heli_Transport_04_bench_F",
        "O_Heli_Attack_02_dynamicLoadout_F"
    ];
};

opfor_air = _airVehicles select [0, (6 min count _airVehicles)];
if (opfor_air isEqualTo []) then {
    opfor_air = [
        "O_Plane_CAS_02_dynamicLoadout_F",
        "O_Plane_Fighter_02_F"
    ];
};
