private _start = diag_tickTime;
if (isServer) then {["init_buildings.sqf initialising...", "CIVREP"] call KPLIB_fnc_log;};

switch (worldName) do {
    case "Chernarus": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\chernarus.sqf"};
    case "cup_chernarus_A3": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\chernarus2020.sqf"};
    case "Enoch": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\enoch.sqf"};
    case "gm_weferlingen_summer": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\gm_weferlingen_summer.sqf"};
    case "gm_weferlingen_winter": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\gm_weferlingen_winter.sqf"};
    case "lythium": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\lythium.sqf"};
    case "Malden": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\malden.sqf"};
    case "panthera3": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\panthera3.sqf"};
    case "pja310": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\pja310.sqf"};
    case "Sara": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\sara.sqf"};
    case "song_bin_tanh": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\song_bin_tanh.sqf"};
    case "Takistan": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\takistan.sqf"};
    case "Tanoa": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\tanoa.sqf"};
    case "WL_Rosche": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\wl_rosche.sqf"};
    case "xcam_taunus": {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\xcam_taunus.sqf"};
    default {call compile preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\IGNORED\altis.sqf"};
};

KPLIB_cr_sectorbuildings = [];

{
    KPLIB_cr_sectorbuildings pushBack [_x, [_x] call F_cr_getBuildings];
} forEach sectors_capture;

{
    KPLIB_cr_sectorbuildings pushBack [_x, [_x] call F_cr_getBuildings];
} forEach sectors_bigtown;

if (isServer) then {[format ["init_buildings.sqf finished. Time needed: %1 seconds", diag_ticktime - _start], "CIVREP"] call KPLIB_fnc_log;};
if (KPLIB_civrep_debug > 0) then {
    {
        [format ["%1: %2", markerText (_x select 0), (_x select 1)], "CIVREP"] call KPLIB_fnc_log;
    } forEach KPLIB_cr_sectorbuildings;
};
