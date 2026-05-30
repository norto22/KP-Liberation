/*
    KPLIB_fnc_getInOut

    File: fn_getInOut.sqf
    Author: Wyqer - https://github.com/KillahPotatoes
    Date: 2018-08-05
    Last Update: 2018-11-10
    License: GNU General Public License v3.0 - https://www.gnu.org/licenses/gpl-3.0.html

    Description:
        Sets the view distance and the sound volume of the player depending on the current vehicle.
        Also changes the camera view, if functionality is enabled by the player.

    Parameter(s):
        NONE

    Returns:
        Function reached the end [BOOL]
*/

// Player on foot
if (isNull objectParent player) then {
    setViewDistance KPLIB_viewFoot;
    setObjectViewDistance KPLIB_viewFoot;
    1 fadeSound 1;
};

// Player in boat or land vehicle
if (vehicle player isKindOf "LandVehicle" || vehicle player isKindOf "Ship") then {
    setViewDistance KPLIB_viewVeh;
    setObjectViewDistance KPLIB_viewVeh;
    1 fadeSound KPLIB_soundVeh;
    if (difficultyOption "thirdPersonView" == 1) then {
        if (KPLIB_tpv > 1) then {player switchCamera "EXTERNAL";};
    };
};

// Player in air vehicle
if (vehicle player isKindOf "Air") then {
    setViewDistance KPLIB_viewAir;
    setObjectViewDistance KPLIB_viewAir;
    1 fadeSound KPLIB_soundVeh;
    if (difficultyOption "thirdPersonView" == 1) then {
        if (KPLIB_tpv == 1 || KPLIB_tpv == 3) then {player switchCamera "EXTERNAL";};
    };
};

true
