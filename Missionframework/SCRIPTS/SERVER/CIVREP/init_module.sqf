// Functions
// Get buildings count for sector
F_cr_getBuildings = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\FNC\f_kp_cr_getBuildings.sqf";
// Change CR value
F_cr_changeCR = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\FNC\f_kp_cr_changeCR.sqf";
// Reputation gain for liberating a sector
F_cr_liberatedSector = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\FNC\f_kp_cr_liberatedSector.sqf";
// Play random wounded animation on unit
F_cr_woundedAnim = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\FNC\f_kp_cr_woundedAnim.sqf";

// Scripts
// Spawn wounded civilians in a sector
civrep_wounded_civs = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\CIVREP\WOUNDED\civrep_wounded_civs.sqf";
// Count initial buildings on each city and bigtown
execVM "SCRIPTS\SERVER\CIVREP\init_buildings.sqf";
