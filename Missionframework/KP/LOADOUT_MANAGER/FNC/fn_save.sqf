/*
    KPLIB_fnc_save

    File: fn_save.sqf
    Author: Wyqer - https://github.com/KillahPotatoes
    Date: 2018-08-05
    Last Update: 2018-11-10
    License: GNU General Public License v3.0 - https://www.gnu.org/licenses/gpl-3.0.html

    Description:
        Saves the selected settings from the player menu dialog and calls the apply function.

    Parameter(s):
        NONE

    Returns:
        Function reached the end [BOOL]
*/

// Dialog controls
private _dialog = findDisplay 75803;
private _ctrlViewFoot = _dialog displayCtrl 7580310;
private _ctrlViewVeh = _dialog displayCtrl 7580311;
private _ctrlViewAir = _dialog displayCtrl 7580312;
private _ctrlTerrain = _dialog displayCtrl 7580313;
private _ctrlTpv = _dialog displayCtrl 7580314;
private _ctrlRadio = _dialog displayCtrl 7580315;
private _ctrlSliderSound = _dialog displayCtrl 7580317;

// Fetch all selected values
KPLIB_viewFoot = round (parseNumber (ctrlText _ctrlViewFoot));
if (KPLIB_viewFoot == 0) then {KPLIB_viewFoot = 1600;};
KPLIB_viewVeh = round (parseNumber (ctrlText _ctrlViewVeh));
if (KPLIB_viewVeh == 0) then {KPLIB_viewVeh = 1600;};
KPLIB_viewAir = round (parseNumber (ctrlText _ctrlViewAir));
if (KPLIB_viewAir == 0) then {KPLIB_viewAir = 1600;};
KPLIB_terrain = lbCurSel _ctrlTerrain;
KPLIB_tpv = lbCurSel _ctrlTpv;
KPLIB_radio = lbCurSel _ctrlRadio;
KPLIB_soundVeh = (round sliderPosition _ctrlSliderSound) / 100;

// Save settings in user profile
profileNamespace setVariable ["KPLIB_Settings", [KPLIB_viewFoot, KPLIB_viewVeh, KPLIB_viewAir, KPLIB_terrain, KPLIB_tpv, KPLIB_radio, KPLIB_soundVeh]];
saveProfileNamespace;

// Apply settings
[] call KPLIB_fnc_apply;

// Close the dialog
closeDialog 0;

true
