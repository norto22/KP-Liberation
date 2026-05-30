player allowDamage false;
(vehicle player) allowDamage false;
KPLIB_endgame = 1;
sleep 20;

_this call compileFinal preprocessFileLineNumbers "SCRIPTS\CLIENT\UI\end_screen.sqf";
