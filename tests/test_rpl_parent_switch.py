import copy

import SimEngine.Mote.MoteDefines as d
from SimEngine import SimLog
import tests.test_utils as u
from SimEngine.Mote.rpl import RplOFBestLinkPDR

# =========================== helper functions =========================================

def check_all_nodes_send_x(motes, x):
    senders = list(set([
        l['_mote_id'] for l in u.read_log_file([SimLog.LOG_TSCH_TXDONE['type']])
        if l['packet']['type'] == x
    ]))
    assert sorted(senders) == sorted([m.id for m in motes])

def check_all_nodes_x(motes, x):
    logs = list(set([l['_mote_id'] for l in u.read_log_file([x])]))
    assert sorted(logs) == sorted([m.id for m in motes])

# === mote

def check_no_packet_drop():
    assert u.read_log_file(['packet_dropped']) == []


# === secjoin

def secjoin_check_all_nodes_joined(motes):
    check_all_nodes_x(motes, SimLog.LOG_SECJOIN_JOINED['type'])

# === app

def count_num_app_rx(appcounter):
    numrx = 0
    for app_rx in u.read_log_file([SimLog.LOG_APP_RX['type']]):
        if app_rx['appcounter'] == appcounter:
            numrx += 1
    assert numrx == 1

# === RPL

def rpl_check_all_node_prefered_parent(motes):
    """ Verify that each mote has a preferred parent """
    for mote in motes:
        if mote.dagRoot:
            continue
        else:
            assert mote.rpl.getPreferredParent() is not None

def rpl_check_all_node_rank(motes):
    """ Verify that each mote has a rank """
    for mote in motes:
        assert mote.rpl.get_rank() is not None

def rpl_check_all_nodes_send_DIOs(motes):
    check_all_nodes_send_x(motes,'DIO')

def rpl_check_all_motes_send_DAOs(motes):
    senders = list(
        set([l['_mote_id']
            for l in u.read_log_file([SimLog.LOG_TSCH_TXDONE['type']])
            if l['packet']['type'] == 'DAO'])
        )
    assert sorted(senders) == sorted([m.id for m in motes if m.id != 0])


# === TSCH

def tsch_check_all_nodes_synced(motes):
    check_all_nodes_x(motes, SimLog.LOG_TSCH_SYNCED['type'])

def tsch_check_all_nodes_send_EBs(motes):
    check_all_nodes_send_x(motes, 'EB')

def tsch_all_nodes_check_dedicated_cell(motes):
    """ Verify that each mote has at least one cell with its preferred parent (TX and/or RX)"""
    for mote in motes:
        if mote.dagRoot:
            continue

        parent = mote.rpl.getPreferredParent()

        # at least one dedicated cell to its preferred parent, which has the TX
        # bit on
        tx_cells = [cell for cell in mote.tsch.get_cells(parent, mote.sf.SLOTFRAME_HANDLE_NEGOTIATED_CELLS) if d.CELLOPTION_TX in cell.options]

        assert len(tx_cells) > 0


def test_free_run(sim_engine):
    sim_engine = sim_engine(
        diff_config = {'rpl_of': 'OFBestLinkPDR'} #diff_config = {'rpl_of': 'OF0'}
    )
    u.run_until_end(sim_engine)


def test_parent_selection(sim_engine):
    sim_engine = sim_engine(
        diff_config = {
            'exec_numMotes'  : 6,
            'conn_class'     : 'FullyMeshed',
            'phy_numChans'   : 1,
            'rpl_of'         : 'OFBestLinkPDR',
            'secjoin_enabled': False
        }
    )

# =========================== Network Topology =========================================
    # shorthands
    connectivity_matrix = sim_engine.connectivity.matrix
    mote_0 = sim_engine.motes[0]
    mote_1 = sim_engine.motes[1]
    mote_2 = sim_engine.motes[2]
    mote_3 = sim_engine.motes[3]
    mote_4 = sim_engine.motes[4]
    mote_5 = sim_engine.motes[5]
    channel = d.TSCH_HOPPING_SEQUENCE[0]

    # The topology of the desired TSCH network is given below, () denotes link PDR:
    #
    #         [mote_0]
    #        /        \
    #     (1.0)        \
    #      /            \
    # [mote_1]         (0.45)
    #     |               \
    #   (1.0)              \
    #     |                 \
    # [mote_2]           [mote_4]   
    #     |                 /
    #   (1.0)              /
    #     |               /
    # [mote_3]         (0.45)
    #      \            /
    #     (1.0)        /
    #        \        /
    #         [mote_5]


    #------disabling Links------#
    # disable the link between mote 0 and mote 5
    connectivity_matrix.set_pdr_both_directions(
        mote_0.id, mote_5.id, channel, 0.0
    )
    # disable the link between mote 1 and mote 5
    connectivity_matrix.set_pdr_both_directions(
        mote_1.id, mote_5.id, channel, 0.0
    )
    # disable the link between mote 2 and mote 5
    connectivity_matrix.set_pdr_both_directions(
        mote_2.id, mote_5.id, channel, 0.0
    )

    # disable the link between mote 0 and mote 2
    connectivity_matrix.set_pdr_both_directions(
        mote_0.id, mote_2.id, channel, 0.0
    )

    # disable the link between mote 0 and mote 3
    connectivity_matrix.set_pdr_both_directions(
        mote_0.id, mote_3.id, channel, 0.0
    )

    # disable the link between mote 1 and mote 4
    connectivity_matrix.set_pdr_both_directions(
        mote_1.id, mote_4.id, channel, 0.0
    )

    # disable the link between mote 2 and mote 4
    connectivity_matrix.set_pdr_both_directions(
        mote_2.id, mote_4.id, channel, 0.0
    )

    # disable the link between mote 3 and mote 4
    connectivity_matrix.set_pdr_both_directions(
        mote_3.id, mote_4.id, channel, 0.0
    )


    # degrade link PDRs to 1.5*ACCEPTABLE_LOWEST_PDR
    # - between mote 0 and mote 4
    # - between mote 4 and mote 5
    connectivity_matrix.set_pdr_both_directions(
        mote_0.id,
        mote_4.id,
        channel,
        RplOFBestLinkPDR.ACCEPTABLE_LOWEST_PDR*1.5
    )
    connectivity_matrix.set_pdr_both_directions(
        mote_4.id,
        mote_5.id,
        channel,
        RplOFBestLinkPDR.ACCEPTABLE_LOWEST_PDR*1.5
    )

# =========================== Network Joining =========================================

    # get all the motes synchronized
    eb = mote_0.tsch._create_EB()
    eb_dummy = {
        'type':            d.PKT_TYPE_EB,
        'mac': {
            'srcMac':      '00-00-00-AA-AA-AA',     # dummy
            'dstMac':      d.BROADCAST_ADDRESS,     # broadcast
            'join_metric': 1000
        }
    }
    mote_1.tsch._action_receiveEB(eb)
    mote_1.tsch._action_receiveEB(eb_dummy)
    mote_2.tsch._action_receiveEB(eb)
    mote_2.tsch._action_receiveEB(eb_dummy)
    mote_3.tsch._action_receiveEB(eb)
    mote_3.tsch._action_receiveEB(eb_dummy)
    mote_4.tsch._action_receiveEB(eb)
    mote_4.tsch._action_receiveEB(eb_dummy)
    mote_5.tsch._action_receiveEB(eb)
    mote_5.tsch._action_receiveEB(eb_dummy)

    # make sure all the motes don't have their parents
    for mote in sim_engine.motes:
        assert mote.rpl.getPreferredParent() is None

    # Parent Selection
    # step 1: make mote_1 and mote_4 connect to mote_0
    dio = u.create_dio(mote_0)
    mote_1.sixlowpan.recvPacket(dio)
    mote_4.sixlowpan.recvPacket(dio)
    assert mote_1.rpl.of.preferred_parent['mote_id'] == mote_0.id
    assert mote_4.rpl.of.preferred_parent['mote_id'] == mote_0.id

    # step 2: give a DIO of mote_1 to mote_2; then mote_2 should
    # selects its parent to mote_1
    dio = u.create_dio(mote_1)
    mote_2.sixlowpan.recvPacket(dio)
    assert mote_2.rpl.of.preferred_parent['mote_id'] == mote_1.id

    # step 3: give a DIO of mote_2 to mote_3; mote_3 should select
    # its parent as mote_2
    dio = u.create_dio(mote_2)
    mote_3.sixlowpan.recvPacket(dio)
    assert mote_3.rpl.of.preferred_parent['mote_id'] == mote_2.id

    # step 4: give a DIO of mote_3 to mote_5; mote_5 should select
    # its parent as mote_3
    dio = u.create_dio(mote_3)
    mote_5.sixlowpan.recvPacket(dio)
    assert mote_5.rpl.of.preferred_parent['mote_id'] == mote_3.id

    # step 5: give a DIO of mote_4 to mote_5; mote_5 should stay
    # with parent as mote_3
    dio = u.create_dio(mote_4)
    mote_5.sixlowpan.recvPacket(dio)
    assert mote_5.rpl.of.preferred_parent['mote_id'] == mote_3.id


    #----- Network Formation -----#

     # verify no packets yet received by root
    assert len(u.read_log_file([SimLog.LOG_APP_RX['type']])) == 0

    # give the network time to form
    u.run_until_asn(sim_engine,30000)

    # verify no packet was dropped
    #check_no_packet_drop()

    # verify that all nodes are sync'ed
    tsch_check_all_nodes_synced(sim_engine.motes)

    # verify that all nodes are join'ed
    secjoin_check_all_nodes_joined(sim_engine.motes)

    #(Optional)
    # verify that all nodes have acquired rank and preferred parent
    #rpl_check_all_node_prefered_parent(sim_engine.motes)
    #rpl_check_all_node_rank(sim_engine.motes)

    # verify that all nodes are sending EBs, DIOs and DAOs
    #tsch_check_all_nodes_send_EBs(sim_engine.motes)
    #rpl_check_all_nodes_send_DIOs(sim_engine.motes)
    #rpl_check_all_motes_send_DAOs(sim_engine.motes)


# =========================== UL/DL Traffic =========================================

    # pick a "datamote" which will send/receive data
    datamote = sim_engine.motes[5] # pick furthest mote

    # get the DAG root
    assert sim_engine.DAGROOT_ID == mote_0.id
    dagroot  = sim_engine.motes[sim_engine.DAGROOT_ID]

   

    #u.run_until_asn(sim_engine,sim_engine.getAsn() + 10000)

    #UL
    for _ in range(10):

            # inject data at the datamote
            datamote.app._send_a_single_packet()

            # give the data time to reach the root
            #u.run_until_asn(sim_engine, sim_engine.getAsn() + 10000)

    #DL
    for _ in range(10):

            # inject data at the root
            dagroot.app._send_ack(datamote.id)

            # give the data time to reach the datamote
            #u.run_until_asn(sim_engine, sim_engine.getAsn() + 10000)

# =========================== Connectivity Matrix Update =========================================
# The Updated Links metrices are given below, () denotes link PDR:
    #
    #         [mote_0]
    #        /        \
    #     (0.3)        \
    #      /            \
    # [mote_1]         (0.75)
    #     |               \
    #   (0.3)              \
    #     |                 \
    # [mote_2]           [mote_4]   
    #     |                 /
    #   (0.3)              /
    #     |               /
    # [mote_3]         (0.75)
    #      \            /
    #     (0.3)        /
    #        \        /
    #         [mote_5]

# degrade link PDRs below ACCEPTABLE_LOWEST_PDR
    # - between mote 0 and mote 1
    # - between mote 1 and mote 2
    # - between mote 2 and mote 3
    # - between mote 3 and mote 5

    connectivity_matrix.set_pdr_both_directions(
        mote_0.id,
        mote_1.id,
        channel,
        RplOFBestLinkPDR.ACCEPTABLE_LOWEST_PDR*0.8
    )

    connectivity_matrix.set_pdr_both_directions(
        mote_1.id,
        mote_2.id,
        channel,
        RplOFBestLinkPDR.ACCEPTABLE_LOWEST_PDR*0.8
    )

    connectivity_matrix.set_pdr_both_directions(
        mote_2.id,
        mote_3.id,
        channel,
        RplOFBestLinkPDR.ACCEPTABLE_LOWEST_PDR*0.8
    )

    connectivity_matrix.set_pdr_both_directions(
        mote_3.id,
        mote_5.id,
        channel,
        RplOFBestLinkPDR.ACCEPTABLE_LOWEST_PDR*0.8
    )


    # Upgrade link PDRs to 2.5*ACCEPTABLE_LOWEST_PDR
    # - between mote 0 and mote 4
    # - between mote 4 and mote 5
    connectivity_matrix.set_pdr_both_directions(
        mote_0.id,
        mote_4.id,
        channel,
        RplOFBestLinkPDR.ACCEPTABLE_LOWEST_PDR*2.5
    )
    connectivity_matrix.set_pdr_both_directions(
        mote_4.id,
        mote_5.id,
        channel,
        RplOFBestLinkPDR.ACCEPTABLE_LOWEST_PDR*2.5
    )

    assert mote_5.rpl.of.preferred_parent['mote_id'] == mote_3.id
    u.run_until_asn(sim_engine, 80000)

    assert mote_5.rpl.of.preferred_parent['mote_id'] == mote_4.id


# =========================== UL/DL After =========================================

    # pick a "datamote" which will send/receive data
    datamote = sim_engine.motes[5] # pick furthest mote

    # get the DAG root
    assert sim_engine.DAGROOT_ID == mote_0.id
    dagroot  = sim_engine.motes[sim_engine.DAGROOT_ID]

   

    #u.run_until_asn(sim_engine,sim_engine.getAsn() + 10000)

    #UL
    for _ in range(10):

            # inject data at the datamote
            datamote.app._send_a_single_packet()

            # give the data time to reach the root
            #u.run_until_asn(sim_engine, sim_engine.getAsn() + 10000)

    #DL
    for _ in range(10):

            # inject data at the root
            dagroot.app._send_ack(datamote.id)

            # give the data time to reach the datamote
            #u.run_until_asn(sim_engine, sim_engine.getAsn() + 10000)

    u.run_until_end(sim_engine)