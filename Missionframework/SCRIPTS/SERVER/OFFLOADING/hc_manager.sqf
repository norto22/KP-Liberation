add_civ_waypoints = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\add_civ_waypoints.sqf";
add_defense_waypoints = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\add_defense_waypoints.sqf";
battlegroup_ai = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\battlegroup_ai.sqf";
building_defence_ai = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\building_defence_ai.sqf";
patrol_ai = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\patrol_ai.sqf";
prisonner_ai = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\prisonner_ai.sqf";
troup_transport = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\AI\troup_transport.sqf";

ied_manager = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECTOR\ied_manager.sqf";
manage_one_sector = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECTOR\manage_one_sector.sqf";
wait_to_spawn_sector = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\SECTOR\wait_to_spawn_sector.sqf";
manage_asymIED = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\ASYMMETRIC\IED\manage_asymIED.sqf";
sector_guerilla = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\ASYMMETRIC\RANDOM\sector_guerilla.sqf";
asym_sector_ambush = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\ASYMMETRIC\RANDOM\asym_sector_ambush.sqf";
civinfo_task = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\CIVINFORMANT\TASKS\civinfo_task.sqf";

execVM "SCRIPTS\CLIENT\MISC\synchronise_vars.sqf";
execVM "SCRIPTS\CLIENT\MISC\synchronise_eco.sqf";
execVM "SCRIPTS\SERVER\OFFLOADING\show_fps.sqf";
