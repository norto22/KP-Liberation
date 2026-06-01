// Scripts
// Logistic convoy ambush
logistic_convoy_ambush = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\ASYMMETRIC\CONVOY\logistic_convoy_ambush.sqf";
// IED spawner for blufor sectors
manage_asymIED = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\ASYMMETRIC\IED\manage_asymIED.sqf";
// Spawner for guerilla ambushes in blufor sectors
asym_sector_ambush = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\ASYMMETRIC\RANDOM\asym_sector_ambush.sqf";
// Spawner for guerilla forces who join a fight at an opfor sector
sector_guerilla = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\ASYMMETRIC\RANDOM\sector_guerilla.sqf";

// Globals
// List sectors which are just liberated. Preventing direct ambush spawn.
asymm_blocked_sectors = [];
publicVariable "asymm_blocked_sectors";

// Start module loop
execVM "SCRIPTS\SERVER\ASYMMETRIC\asymmetric_loop.sqf";
