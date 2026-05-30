_idact = -1;
while { true } do {
	waitUntil{ sleep 0.3; alive player };
	_idact = player addAction ["<t color='#FF8000'>" + localize "STR_KPLIB_GREUH_EXTENDED_OPTIONS_ACTIONMENU" + "</t>","GREUH\scripts\GREUH_dialog.sqf","",-1000,false,true];
	waitUntil{ sleep 0.3; !alive player};
};