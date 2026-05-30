// AI
add_civ_waypoints = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\add_civ_waypoints.sqf";
add_defense_waypoints = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\add_defense_waypoints.sqf";
battlegroup_ai = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\battlegroup_ai.sqf";
building_defence_ai = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\building_defence_ai.sqf";
patrol_ai = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\patrol_ai.sqf";
prisonner_ai = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\prisonner_ai.sqf";
troup_transport = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\troup_transport.sqf";

// Battlegroup
spawn_air = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\BATTLEGROUP\spawn_air.sqf";
spawn_battlegroup = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\BATTLEGROUP\spawn_battlegroup.sqf";

// Game
check_victory_conditions = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\GAME\check_victory_conditions.sqf";

// Patrol
manage_one_civilian_patrol = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\PATROLS\manage_one_civilian_patrol.sqf";
manage_one_patrol = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\PATROLS\manage_one_patrol.sqf";
reinforcements_manager = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\PATROLS\reinforcements_manager.sqf";
send_paratroopers = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\PATROLS\send_paratroopers.sqf";

// Secondary objectives
fob_hunting = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECONDARY\fob_hunting.sqf";
convoy_hijack = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECONDARY\convoy_hijack.sqf";
search_and_rescue = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECONDARY\search_and_rescue.sqf";

// Sector
attack_in_progress_fob = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECTOR\attack_in_progress_fob.sqf";
attack_in_progress_sector = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECTOR\attack_in_progress_sector.sqf";
ied_manager = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECTOR\ied_manager.sqf";
manage_one_sector = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECTOR\manage_one_sector.sqf";
wait_to_spawn_sector = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECTOR\wait_to_spawn_sector.sqf";

// Globals
active_sectors = []; publicVariable "active_sectors";

execVM "SCRIPTS\SERVER\BASE\startgame.sqf";
execVM "SCRIPTS\SERVER\BASE\huron_manager.sqf";
execVM "SCRIPTS\SERVER\BASE\startvehicle_spawn.sqf";
[] call KPLIB_fnc_createSuppModules;
execVM "SCRIPTS\SERVER\BATTLEGROUP\counter_battlegroup.sqf";
execVM "SCRIPTS\SERVER\BATTLEGROUP\random_battlegroups.sqf";
execVM "SCRIPTS\SERVER\BATTLEGROUP\readiness_increase.sqf";
execVM "SCRIPTS\SERVER\GAME\apply_default_permissions.sqf";
execVM "SCRIPTS\SERVER\GAME\cleanup_vehicles.sqf";
if (!KPLIB_fog_param) then {execVM "SCRIPTS\SERVER\GAME\set_fog.sqf";};
execVM "SCRIPTS\SERVER\GAME\manage_time.sqf";
execVM "SCRIPTS\SERVER\GAME\manage_weather.sqf";
execVM "SCRIPTS\SERVER\GAME\playtime.sqf";
execVM "SCRIPTS\SERVER\GAME\save_manager.sqf";
execVM "SCRIPTS\SERVER\GAME\spawn_radio_towers.sqf";
execVM "SCRIPTS\SERVER\GAME\synchronise_vars.sqf";
execVM "SCRIPTS\SERVER\GAME\synchronise_eco.sqf";
execVM "SCRIPTS\SERVER\GAME\zeus_synchro.sqf";
execVM "SCRIPTS\SERVER\OFFLOADING\show_fps.sqf";
execVM "SCRIPTS\SERVER\PATROLS\civilian_patrols.sqf";
execVM "SCRIPTS\SERVER\PATROLS\manage_patrols.sqf";
execVM "SCRIPTS\SERVER\PATROLS\reinforcements_resetter.sqf";
if (KPLIB_ailogistics) then {execVM "SCRIPTS\SERVER\RESOURCES\manage_logistics.sqf";};
execVM "SCRIPTS\SERVER\RESOURCES\manage_resources.sqf";
execVM "SCRIPTS\SERVER\RESOURCES\recalculate_resources.sqf";
execVM "SCRIPTS\SERVER\RESOURCES\recalculate_timer.sqf";
execVM "SCRIPTS\SERVER\RESOURCES\recalculate_timer_sector.sqf";
execVM "SCRIPTS\SERVER\RESOURCES\unit_cap.sqf";
execVM "SCRIPTS\SERVER\SECTOR\lose_sectors.sqf";

KPLIB_fsm_sectorMonitor = [] call KPLIB_fnc_sectorMonitor;
if (KPLIB_high_command) then {KPLIB_fsm_highcommand = [] call KPLIB_fnc_highcommand;};

// Select FOB templates
switch (KPLIB_preset_opfor) do {
    case 1: {
        KPLIB_fob_templates = [
            "scripts\fob_templates\apex\template1.sqf",
            "scripts\fob_templates\apex\template2.sqf",
            "scripts\fob_templates\apex\template3.sqf",
            "scripts\fob_templates\apex\template4.sqf",
            "scripts\fob_templates\apex\template5.sqf"
        ];
    };
    case 12: {
        KPLIB_fob_templates = [
            "scripts\fob_templates\unsung\template1.sqf",
            "scripts\fob_templates\unsung\template2.sqf",
            "scripts\fob_templates\unsung\template3.sqf",
            "scripts\fob_templates\unsung\template4.sqf",
            "scripts\fob_templates\unsung\template5.sqf"
        ];
    };
    default {
        KPLIB_fob_templates = [
            "scripts\fob_templates\default\template1.sqf",
            "scripts\fob_templates\default\template2.sqf",
            "scripts\fob_templates\default\template3.sqf",
            "scripts\fob_templates\default\template4.sqf",
            "scripts\fob_templates\default\template5.sqf",
            "scripts\fob_templates\default\template6.sqf",
            "scripts\fob_templates\default\template7.sqf",
            "scripts\fob_templates\default\template8.sqf",
            "scripts\fob_templates\default\template9.sqf",
            "scripts\fob_templates\default\template10.sqf"
        ];
    };
};

// Civil Reputation
execVM "SCRIPTS\SERVER\CIVREP\init_module.sqf";

// Civil Informant
execVM "SCRIPTS\SERVER\CIVINFORMANT\init_module.sqf";

// Asymmetric Threats
execVM "SCRIPTS\SERVER\ASYMMETRIC\init_module.sqf";

// Groupcheck for deletion when empty
execVM "SCRIPTS\SERVER\OFFLOADING\group_diag.sqf";

{
    if ((_x != player) && (_x distance (markerPos KPLIB_respawn_marker) < 200 )) then {
        deleteVehicle _x;
    };
} forEach allUnits;

// Server Restart Script from K4s0
if (KPLIB_restart > 0) then {
    execVM "SCRIPTS\SERVER\GAME\server_restart.sqf";
};
