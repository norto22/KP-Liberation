/*
    TIOW2 Arsenal Preset

    Needed Mods:
    - CBA_A3
    - Weapon Eventhandler Framework
    - There is Only War Mod - Release 5 BETA
    - TIOW2

    Space Marine armor is intentionally not curated here. The TIOW2 Workshop page
    notes that Space Marines must be spawned as units and their armor cannot be
    equipped onto regular Arma soldiers through Virtual Arsenal.
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

KPLIB_arsenal_weapons = ("true" configClasses (configFile >> "CfgWeapons")) select {
    ((getNumber (_x >> "scope")) >= 2) &&
    {[_x] call _isTiowConfig} &&
    {private _type = getNumber (_x >> "type"); _type in [1, 2, 4, 4096]}
} apply {configName _x};

KPLIB_arsenal_magazines = ("true" configClasses (configFile >> "CfgMagazines")) select {
    ((getNumber (_x >> "scope")) >= 2) && {[_x] call _isTiowConfig}
} apply {configName _x};

KPLIB_arsenal_items = ("true" configClasses (configFile >> "CfgWeapons")) select {
    ((getNumber (_x >> "scope")) >= 2) &&
    {[_x] call _isTiowConfig} &&
    {private _type = getNumber (_x >> "type"); !(_type in [1, 2, 4, 4096])} &&
    {private _name = toLower getText (_x >> "displayName"); ((_name find "space marine") < 0) && {(_name find "astartes") < 0}}
} apply {configName _x};

KPLIB_arsenal_backpacks = ("true" configClasses (configFile >> "CfgVehicles")) select {
    ((getNumber (_x >> "scope")) >= 2) &&
    {[_x] call _isTiowConfig} &&
    {(configName _x) isKindOf "Bag_Base"}
} apply {configName _x};
