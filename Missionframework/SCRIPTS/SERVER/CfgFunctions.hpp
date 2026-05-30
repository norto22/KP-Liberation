class server_highcommand {
    file = "SCRIPTS\SERVER\HIGHCOMMAND";

    class highcommand                   {ext = ".fsm";};
};

class server_sector {
    file = "SCRIPTS\SERVER\SECTOR";

    class destroyFob                    {};
    class sectorMonitor                 {ext = ".fsm";};
    class spawnSectorCrates             {};
    class spawnSectorIntel              {};
};

class server_support {
    file = "SCRIPTS\SERVER\SUPPORT";

    class createSuppModules             {};
};
