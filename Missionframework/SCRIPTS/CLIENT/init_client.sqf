[] call compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\MISC\init_markers.sqf";
switch (KPLIB_arsenal) do {
    case  1: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\custom.sqf";};
    case  2: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\rhsusaf.sqf";};
    case  3: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\3cbBAF.sqf";};
    case  4: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\gm_west.sqf";};
    case  5: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\gm_east.sqf";};
    case  6: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\csat.sqf";};
    case  7: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\unsung.sqf";};
    case  8: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\sfp.sqf";};
    case  9: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\bwmod.sqf";};
    case  10: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\vanilla_nato_mtp.sqf";};
    case  11: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\vanilla_nato_tropic.sqf";};
    case  12: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\vanilla_nato_wdl.sqf";};
    case  13: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\vanilla_csat_hex.sqf";};
    case  14: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\vanilla_csat_ghex.sqf";};
    case  15: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\vanilla_aaf.sqf";};
    case  16: {[] call compileFinal preprocessFileLineNumbers "ARSENAL_PRESETS\vanilla_ldf.sqf";};
    default  {KPLIB_arsenal_weapons = [];KPLIB_arsenal_magazines = [];KPLIB_arsenal_items = [];KPLIB_arsenal_backpacks = [];};
};

if (typeOf player == "VirtualSpectator_F") exitWith {
    execVM "SCRIPTS\CLIENT\MARKERS\empty_vehicles_marker.sqf";
    execVM "SCRIPTS\CLIENT\MARKERS\fob_markers.sqf";
    execVM "SCRIPTS\CLIENT\MARKERS\group_icons.sqf";
    execVM "SCRIPTS\CLIENT\MARKERS\hostile_groups.sqf";
    execVM "SCRIPTS\CLIENT\MARKERS\sector_manager.sqf";
    execVM "SCRIPTS\CLIENT\MARKERS\spot_timer.sqf";
    execVM "SCRIPTS\CLIENT\MISC\synchronise_vars.sqf";
    execVM "SCRIPTS\CLIENT\UI\ui_manager.sqf";
};

// This causes the script error with not defined variable _display in File A3\functions_f_bootcamp\Inventory\fn_arsenal.sqf [BIS_fnc_arsenal], line 2122
// ["Preload"] call BIS_fnc_arsenal;
spawn_camera = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\SPAWN\spawn_camera.sqf";
cinematic_camera = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\UI\cinematic_camera.sqf";
write_credit_line = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\UI\write_credit_line.sqf";
do_load_box = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\AMMOBOXES\do_load_box.sqf";
kp_fuel_consumption = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\MISC\kp_fuel_consumption.sqf";
kp_vehicle_permissions = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\MISC\vehicle_permissions.sqf";

execVM "SCRIPTS\CLIENT\ACTIONS\intel_manager.sqf";
execVM "SCRIPTS\CLIENT\ACTIONS\recycle_manager.sqf";
execVM "SCRIPTS\CLIENT\ACTIONS\unflip_manager.sqf";
execVM "SCRIPTS\CLIENT\AMMOBOXES\ammobox_action_manager.sqf";
execVM "SCRIPTS\CLIENT\BUILD\build_overlay.sqf";
execVM "SCRIPTS\CLIENT\BUILD\do_build.sqf";
execVM "SCRIPTS\CLIENT\COMMANDER\enforce_whitelist.sqf";
if (KPLIB_mapmarkers) then {execVM "SCRIPTS\CLIENT\MARKERS\empty_vehicles_marker.sqf";};
execVM "SCRIPTS\CLIENT\MARKERS\fob_markers.sqf";
if (!KPLIB_high_command && KPLIB_mapmarkers) then {execVM "SCRIPTS\CLIENT\MARKERS\group_icons.sqf";};
execVM "SCRIPTS\CLIENT\MARKERS\hostile_groups.sqf";
if (KPLIB_mapmarkers) then {execVM "SCRIPTS\CLIENT\MARKERS\huron_marker.sqf";} else {deleteMarkerLocal "huronmarker"};
execVM "SCRIPTS\CLIENT\MARKERS\sector_manager.sqf";
execVM "SCRIPTS\CLIENT\MARKERS\spot_timer.sqf";
execVM "SCRIPTS\CLIENT\MISC\broadcast_squad_colors.sqf";
execVM "SCRIPTS\CLIENT\MISC\init_arsenal.sqf";
execVM "SCRIPTS\CLIENT\MISC\permissions_warning.sqf";
if (!KPLIB_ace) then {execVM "SCRIPTS\CLIENT\MISC\resupply_manager.sqf";};
execVM "SCRIPTS\CLIENT\MISC\secondary_jip.sqf";
execVM "SCRIPTS\CLIENT\MISC\synchronise_vars.sqf";
execVM "SCRIPTS\CLIENT\MISC\synchronise_eco.sqf";
execVM "SCRIPTS\CLIENT\MISC\playerNamespace.sqf";
execVM "SCRIPTS\CLIENT\SPAWN\redeploy_manager.sqf";
execVM "SCRIPTS\CLIENT\UI\ui_manager.sqf";
execVM "SCRIPTS\CLIENT\UI\tutorial_manager.sqf";
execVM "SCRIPTS\CLIENT\MARKERS\update_production_sites.sqf";

player addMPEventHandler ["MPKilled", {_this spawn kill_manager;}];
player addEventHandler ["GetInMan", {[_this select 2] spawn kp_fuel_consumption;}];
player addEventHandler ["GetInMan", {[_this select 2] call KPLIB_fnc_setVehiclesSeized;}];
player addEventHandler ["GetInMan", {[_this select 2] call KPLIB_fnc_setVehicleCaptured;}];
player addEventHandler ["GetInMan", {[_this select 2] call kp_vehicle_permissions;}];
player addEventHandler ["SeatSwitchedMan", {[_this select 2] call kp_vehicle_permissions;}];
player addEventHandler ["HandleRating", {if ((_this select 1) < 0) then {0};}];

// Disable stamina, if selected in parameter
if (!KPLIB_fatigue) then {
    player enableStamina false;
    player addEventHandler ["Respawn", {player enableStamina false;}];
};

// Reduce aim precision coefficient, if selected in parameter
if (!KPLIB_sway) then {
    player setCustomAimCoef 0.1;
    player addEventHandler ["Respawn", {player setCustomAimCoef 0.1;}];
};

execVM "SCRIPTS\CLIENT\UI\intro.sqf";

[player] joinSilent (createGroup [KPLIB_side_friendly, true]);

// Commander init
if (player isEqualTo ([] call KPLIB_fnc_getCommander)) then {
    // Start tutorial
    if (KPLIB_tutorial) then {
        [] call KPLIB_fnc_tutorial;
    };
    // Request Zeus if enabled
    if (KPLIB_commander_zeus) then {
        [] spawn {
            sleep 5;
            [] call KPLIB_fnc_requestZeus;
        };
    };
};
