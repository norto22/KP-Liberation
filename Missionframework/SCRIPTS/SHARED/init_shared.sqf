kill_manager = compileFinal preprocessFileLineNumbers "SCRIPTS\SHARED\kill_manager.sqf";

build_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\build_remote_call.sqf";
build_fob_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\build_fob_remote_call.sqf";
cancel_build_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\cancel_build_remote_call.sqf";
prisonner_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\prisonner_remote_call.sqf";
recycle_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\recycle_remote_call.sqf";
reinforcements_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\reinforcements_remote_call.sqf";
sector_liberated_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\sector_liberated_remote_call.sqf";
intel_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\intel_remote_call.sqf";
start_secondary_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\start_secondary_remote_call.sqf";
change_prod_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\change_prod_remote_call.sqf";
build_fac_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\build_fac_remote_call.sqf";
if (KPLIB_ailogistics) then {
    add_logiGroup_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\add_logiGroup_remote_call.sqf";
    del_logiGroup_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\del_logiGroup_remote_call.sqf";
    add_logiTruck_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\add_logiTruck_remote_call.sqf";
    del_logiTruck_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\del_logiTruck_remote_call.sqf";
    save_logi_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\save_logi_remote_call.sqf";
    abort_logi_remote_call = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\REMOTECALL\abort_logi_remote_call.sqf";
};

remote_call_sector = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\REMOTECALL\remote_call_sector.sqf";
remote_call_fob = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\REMOTECALL\remote_call_fob.sqf";
remote_call_battlegroup = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\REMOTECALL\remote_call_battlegroup.sqf";
remote_call_endgame = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\REMOTECALL\remote_call_endgame.sqf";
remote_call_prisonner = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\REMOTECALL\remote_call_prisonner.sqf";
remote_call_intel = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\REMOTECALL\remote_call_intel.sqf";
remote_call_incoming = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\REMOTECALL\remote_call_incoming.sqf";

civinfo_notifications = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\CIVINFORMANT\civinfo_notifications.sqf";
civinfo_escort = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\CIVINFORMANT\civinfo_escort.sqf";
civinfo_delivered = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\CIVINFORMANT\civinfo_delivered.sqf";

asymm_notifications = compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\ASYMMETRIC\asymm_notifications.sqf";

execVM "SCRIPTS\SHARED\diagnostics.sqf";
