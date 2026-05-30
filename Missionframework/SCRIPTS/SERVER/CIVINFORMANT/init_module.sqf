// Scripts
// Task selection and spawning
civinfo_task = compileFinal preprocessFileLineNumbers "SCRIPTS\SERVER\CIVINFORMANT\TASKS\civinfo_task.sqf";

// Start spawn loop
execVM "SCRIPTS\SERVER\CIVINFORMANT\civinfo_loop.sqf";
