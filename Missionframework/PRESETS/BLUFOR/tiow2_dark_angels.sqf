/*
    TIOW2 Dark Angels BLUFOR Preset

    Uses hardcoded classnames exported from Arma 3 with:
    CBA_A3, Weapon Eventhandler Framework, There is Only War Mod - Release 5 BETA and TIOW2.
*/

// Civilian classnames.
civilians = [
    "C_man_1",
    "C_man_1_1_F",
    "C_man_1_2_F",
    "C_man_1_3_F",
    "C_man_polo_1_F",
    "C_man_polo_2_F",
    "C_man_polo_3_F",
    "C_man_polo_4_F",
    "C_man_polo_5_F",
    "C_man_polo_6_F"
];

// FOB and support logistics.
FOB_typename = "Land_Cargo_HQ_V1_F";
FOB_box_typename = "B_Slingload_01_Cargo_F";
FOB_truck_typename = "TIOW_SM_Rhino_DA";
Arsenal_typename = "B_supplyCrate_F";
Respawn_truck_typename = "B_Truck_01_medical_F";
huron_typename = "B_Heli_Transport_03_unarmed_F";

crewman_classname = "TIOW_Tactical_DA_1";
pilot_classname = "TIOW_Tactical_DA_1";

KPLIB_little_bird_classname = "TIOW_DA_Tornado";
KPLIB_boat_classname = "B_Boat_Transport_01_F";
KPLIB_truck_classname = "TIOW_SM_Rhino_DA";

KPLIB_small_storage_building = "ContainmentArea_02_sand_F";
KPLIB_large_storage_building = "ContainmentArea_01_sand_F";
KPLIB_recycle_building = "Land_RepairDepot_01_tan_F";
KPLIB_air_vehicle_building = "B_Radar_System_01_F";
KPLIB_heli_slot_building = "Land_HelipadSquare_F";
KPLIB_plane_slot_building = "Land_TentHangar_V1_F";

KPLIB_supply_crate = "CargoNet_01_box_F";
KPLIB_ammo_crate = "B_CargoNet_01_ammo_F";
KPLIB_fuel_crate = "CargoNet_01_barrels_F";

infantry_units = [
    ["TIOW_Tactical_DA_1",60,0,0],
    ["TIOW_Tactical_DA_1_Imperialis",60,0,0],
    ["TIOW_Tactical_DA_2",60,0,0],
    ["TIOW_Tactical_DA_3",60,0,0],
    ["TIOW_Tactical_DA_4",60,0,0],
    ["TIOW_Tactical_DA_5",60,0,0],
    ["TIOW_Tactical_DA_6",60,0,0],
    ["TIOW_Tactical_DA_7",60,0,0],
    ["TIOW_HeavyBolter_DA_4",80,25,0],
    ["TIOW_Plasmagunner_DA_5",85,35,0],
    ["TIOW_Meltagunner_DA_3",90,40,0],
    ["TIOW_Sergeant_DA_1",75,20,0],
    ["TIOW_Tactical_DA_HH_1",60,0,0],
    ["TIOW_Tactical_DA_HH_1_Imperialis",60,0,0],
    ["TIOW_Tactical_DA_HH_2",60,0,0],
    ["TIOW_Tactical_DA_HH_3",60,0,0],
    ["TIOW_Tactical_DA_HH_4",60,0,0],
    ["TIOW_Tactical_DA_HH_5",60,0,0],
    ["TIOW_Tactical_DA_HH_6",60,0,0],
    ["TIOW_Tactical_DA_HH_7",60,0,0],
    ["TIOW_HeavyBolter_DA_HH_4",80,25,0],
    ["TIOW_Plasmagunner_DA_HH_5",85,35,0],
    ["TIOW_Meltagunner_DA_HH_3",90,40,0],
    ["TIOW_Sergeant_DA_HH_1",75,20,0]
];

light_vehicles = [
    ["TIOW_Drop_Pod_DA",200,0,100],
    ["TIOW_Drop_Pod_DA_HH",200,0,100],
    ["TIOW_Bike_DA_1",125,50,75],
    ["TIOW_Bike_DA_2",150,80,75],
    ["TIOW_Bike_DA_3",175,100,90],
    ["TIOW_Bike_DA_4",175,120,90],
    ["TIOW_SM_Rhino_DA",250,50,150],
    ["TIOW_SM_Razorback_DA",300,150,175],
    ["TIOW_SM_Razorback_LC_DA",350,225,175],
    ["TIOW_SM_Razorback_AC_DA",350,225,175],
    ["TIOW_DA_Tornado",300,200,150],
    ["TIOW_DA_Typhoon",350,250,175],
    ["TIOW_DA_Storm",325,200,175],
    ["TIOW_DA_Temp",375,300,200]
];

heavy_vehicles = [
    ["TIOW_SM_Predator_DA",500,350,250],
    ["TIOW_SM_Vindicator_DA",550,400,275],
    ["TIOW_SM_Whirlwind_Arty_DA",600,450,275]
];

air_vehicles = [
    ["Thunderhawk_1_DA_TIOW",1200,900,600],
    ["Thunderhawk_1_DA_HH_TIOW",1200,900,600]
];

static_vehicles = [
    ["B_HMG_01_F",25,40,0],
    ["B_GMG_01_F",25,60,0],
    ["B_static_AT_F",50,75,0],
    ["B_Mortar_01_F",80,100,0]
];

buildings = [
    ["Land_BagFence_Round_F",5,0,0],
    ["Land_BagFence_Long_F",5,0,0],
    ["Land_BagBunker_Small_F",25,0,0],
    ["Land_BagBunker_Large_F",50,0,0],
    ["Land_HBarrier_1_F",5,0,0],
    ["Land_HBarrier_3_F",10,0,0],
    ["Land_HBarrier_5_F",15,0,0],
    ["Land_HBarrier_Big_F",20,0,0],
    ["Land_Bunker_01_small_F",100,0,0],
    ["land_tiow_astartes_scale_weapons_rack_d_angels",15,0,0],
    ["land_TIOW_Hab1DarkTan",75,0,0],
    ["land_TIOW_Hab1DarkGrey",75,0,0],
    ["land_TIOW_Hab3DarkTan",125,0,0],
    ["land_TIOW_Hab3DarkGrey",125,0,0],
    ["land_TIOW_Hab4DarkTan",175,0,0],
    ["land_TIOW_Hab4DarkGrey",175,0,0]
];

support_vehicles = [
    ["B_Truck_01_Repair_F",325,0,75],
    ["B_Truck_01_fuel_F",125,0,275],
    ["B_Truck_01_ammo_F",125,200,75],
    ["B_Truck_01_medical_F",125,0,75],
    ["B_APC_Tracked_01_CRV_F",500,250,450]
];

blufor_squad_inf_light = [
    "TIOW_Tactical_DA_1",
    "TIOW_Tactical_DA_3",
    "TIOW_Tactical_DA_5",
    "TIOW_Sergeant_DA_1"
];

blufor_squad_inf = [
    "TIOW_Sergeant_DA_1",
    "TIOW_Tactical_DA_1",
    "TIOW_Tactical_DA_1_Imperialis",
    "TIOW_Tactical_DA_2",
    "TIOW_Tactical_DA_3",
    "TIOW_Tactical_DA_4",
    "TIOW_HeavyBolter_DA_4",
    "TIOW_Plasmagunner_DA_5"
];

blufor_squad_at = [
    "TIOW_Sergeant_DA_1",
    "TIOW_Tactical_DA_1",
    "TIOW_Meltagunner_DA_3",
    "TIOW_Meltagunner_DA_HH_3"
];

blufor_squad_aa = [
    "TIOW_Sergeant_DA_1",
    "TIOW_Tactical_DA_1",
    "TIOW_HeavyBolter_DA_4",
    "TIOW_Plasmagunner_DA_5"
];

blufor_squad_recon = [
    "TIOW_Tactical_DA_6",
    "TIOW_Tactical_DA_7",
    "TIOW_Tactical_DA_3",
    "TIOW_Meltagunner_DA_3",
    "TIOW_Plasmagunner_DA_5",
    "TIOW_Sergeant_DA_1"
];

blufor_squad_para = [
    "TIOW_Sergeant_DA_HH_1",
    "TIOW_Tactical_DA_HH_1",
    "TIOW_Tactical_DA_HH_3",
    "TIOW_Tactical_DA_HH_5",
    "TIOW_HeavyBolter_DA_HH_4",
    "TIOW_Plasmagunner_DA_HH_5"
];

elite_vehicles = [
    "TIOW_SM_Predator_DA",
    "TIOW_SM_Vindicator_DA",
    "TIOW_SM_Whirlwind_Arty_DA",
    "Thunderhawk_1_DA_TIOW",
    "Thunderhawk_1_DA_HH_TIOW"
];
