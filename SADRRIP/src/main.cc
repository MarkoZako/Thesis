#define _BSD_SOURCE

#include <algorithm>
#include <chrono>
#include <random>
#include <vector>
#include <getopt.h>
#include "ooo_cpu.h"
#include "uncore.h"

uint8_t warmup_complete[NUM_CPUS], 
        simulation_complete[NUM_CPUS], 
        all_warmup_complete = 0, 
        all_simulation_complete = 0,
        MAX_INSTR_DESTINATIONS = NUM_INSTR_DESTINATIONS,
        knob_cloudsuite = 0,
        knob_low_bandwidth = 0;

uint64_t warmup_instructions     = 1000000,
         simulation_instructions = 10000000,
  champsim_seed,
  rrip_policies = 0,
  dirty_rrip_policies = 0;		// specifiy policy for SRRIP or policies for SD-DRRIP or SA-DRRIP


uint32_t psel_width = 10;	// specifiy bits for psel counter
uint32_t track_set = -1;	// specifiy set to track (if -1 means no tracking)
uint32_t psel_mask = 15;	// mask indicates what type o fmisses update PSEL 8 W, 4 Pref, 2 RFO, 1 READS


int window = 64;		// window size
int dsalgo = 0;		// 0 drrip classical, 1 is slope
int sr_thr = 32;
int br_thr = 32;
int boost  = 256;
int hit_mask = 7;			// for SA determines which ghits update state analytic counters
uint64_t demote_mask= 0;// for what type of replacements to demote state when looking for a victim
uint32_t max_count_rr = 1; //Fixed Cycles for each core Round robin arbitration (Default: 1 cycle)


int print_RQ = 0;

time_t start_time;

// PAGE TABLE
uint32_t PAGE_TABLE_LATENCY = 0, SWAP_LATENCY = 0;
queue <uint64_t > page_queue;
map <uint64_t, uint64_t> page_table, inverse_table, recent_page, unique_cl[NUM_CPUS];
uint64_t previous_ppage, num_adjacent_page, num_cl[NUM_CPUS], allocated_pages, num_page[NUM_CPUS], minor_fault[NUM_CPUS], major_fault[NUM_CPUS];

void record_roi_stats(uint32_t cpu, CACHE *cache)
{
    for (uint32_t i=0; i<NUM_TYPES; i++) {
        cache->roi_access[cpu][i] = cache->sim_access[cpu][i];
        cache->roi_hit[cpu][i] = cache->sim_hit[cpu][i];
        cache->roi_miss[cpu][i] = cache->sim_miss[cpu][i];
    }
	if(cache->cache_type != 6){
	cache->RQ[0].ACCESS_ROI = cache->RQ[0].ACCESS;
	cache->RQ[0].TO_CACHE_ROI = cache->RQ[0].TO_CACHE;
	cache->RQ[0].MERGED_ROI = cache->RQ[0].MERGED;
	cache->RQ[0].FORWARD_ROI = cache->RQ[0].FORWARD;
	}else if(cache->cache_type == 6){
	for(int i=0;i<NUM_CPUS;i++){
           cache->RQ[i].ACCESS_ROI = cache->RQ[i].ACCESS;
           cache->RQ[i].TO_CACHE_ROI = cache->RQ[i].TO_CACHE;
           cache->RQ[i].MERGED_ROI = cache->RQ[i].MERGED;
           cache->RQ[i].FORWARD_ROI = cache->RQ[i].FORWARD;
	  }
	}
	cache->WQ.ACCESS_ROI = cache->WQ.ACCESS;
        cache->WQ.TO_CACHE_ROI = cache->WQ.TO_CACHE;
        cache->WQ.MERGED_ROI = cache->WQ.MERGED;
        cache->WQ.FORWARD_ROI = cache->WQ.FORWARD;

	//GIANNIS STATISTICS ROI RECORD
	ooo_cpu[cpu].num_loads_ROI = ooo_cpu[cpu].num_loads;
	ooo_cpu[cpu].num_stores_ROI = ooo_cpu[cpu].num_stores;
	ooo_cpu[cpu].total_dest_operands_ROI = ooo_cpu[cpu].total_dest_operands;
	ooo_cpu[cpu].total_source_operands_ROI = ooo_cpu[cpu].total_source_operands;
	ooo_cpu[cpu].DEPENDED_LOADS_ROI = ooo_cpu[cpu].DEPENDED_LOADS;
	ooo_cpu[cpu].SQ_ADDED_ROI = ooo_cpu[cpu].SQ_ADDED;
	ooo_cpu[cpu].LQ_ADDED_ROI = ooo_cpu[cpu].LQ_ADDED;

}

void print_roi_stats(uint32_t cpu, CACHE *cache)
{
    uint64_t TOTAL_ACCESS = 0, TOTAL_HIT = 0, TOTAL_MISS = 0;
    uint64_t TOTAL_ACCESSES = 0, TOTAL_HITS = 0, TOTAL_MISSES = 0;
    uint64_t TOTAL_MSHR_MERGED = 0;

    for (uint32_t i=0; i<NUM_TYPES; i++) {
        TOTAL_ACCESS += cache->roi_access[cpu][i];
        TOTAL_HIT += cache->roi_hit[cpu][i];
        TOTAL_MISS += cache->roi_miss[cpu][i];
	TOTAL_ACCESSES += cache->ACCESS[i];
	TOTAL_HITS += cache->HIT[i];
	TOTAL_MISSES += cache->MISS[i];
	TOTAL_MSHR_MERGED += cache->MSHR_MERGED[i];
    }

    cout << cache->NAME;
    cout << " TOTAL     ACCESS: " << setw(10) << TOTAL_ACCESS << "  HIT: " << setw(10) << TOTAL_HIT << "  MISS: " << setw(10) << TOTAL_MISS << endl;

    cout << cache->NAME;
    cout << " LOAD      ACCESS: " << setw(10) << cache->roi_access[cpu][0] << "  HIT: " << setw(10) << cache->roi_hit[cpu][0] << "  MISS: " << setw(10) << cache->roi_miss[cpu][0] << endl;

    cout << cache->NAME;
    cout << " RFO       ACCESS: " << setw(10) << cache->roi_access[cpu][1] << "  HIT: " << setw(10) << cache->roi_hit[cpu][1] << "  MISS: " << setw(10) << cache->roi_miss[cpu][1] << endl;

    cout << cache->NAME;
    cout << " PREFETCH  ACCESS: " << setw(10) << cache->roi_access[cpu][2] << "  HIT: " << setw(10) << cache->roi_hit[cpu][2] << "  MISS: " << setw(10) << cache->roi_miss[cpu][2] << endl;

    cout << cache->NAME;
    cout << " WRITEBACK ACCESS: " << setw(10) << cache->roi_access[cpu][3] << "  HIT: " << setw(10) << cache->roi_hit[cpu][3] << "  MISS: " << setw(10) << cache->roi_miss[cpu][3] << endl;

    cout << cache->NAME;
    cout << " PREFETCH  REQUESTED: " << setw(10) << cache->pf_requested << "  ISSUED: " << setw(10) << cache->pf_issued;
    cout << "  USEFUL: " << setw(10) << cache->pf_useful << "  USELESS: " << setw(10) << cache->pf_useless << endl;

    cout << cache->NAME;
    cout << " TOTAL MSHR MERGED: " << setw(10) << TOTAL_MSHR_MERGED << endl;

    cout << cache->NAME;
    cout << " LOAD MSHR MERGED: " << setw(10) << cache->MSHR_MERGED[0] << endl;
    
    cout << cache->NAME;
    cout << " RFO MSHR MERGED: " << setw(10) << cache->MSHR_MERGED[1] << endl; 
    
    cout << cache->NAME;
    cout << " PREFETCH MSHR MERGED: " << setw(10) << cache->MSHR_MERGED[2] << endl;
    
    cout << cache->NAME;
    cout << " WRITEBACK MSHR MERGED: " << setw(10) << cache->MSHR_MERGED[3] << endl;

    cout << cache->NAME;
    cout << " TOTAL ACCESSES: " << setw(10) << TOTAL_ACCESSES << " HITS: " << setw(10) << TOTAL_HITS << " MISSES: " << setw(10) << TOTAL_MISSES << endl; 

    cout << cache->NAME;
    cout << " LOAD ACCESSES: " << setw(10) << cache->ACCESS[0] << " HITS: " << setw(10) << cache->HIT[0] << " MISSES: " << setw(10) << cache->MISS[0] << endl;

    cout << cache->NAME;
    cout << " RFO ACCESSES: " << setw(10) << cache->ACCESS[1] << " HITS: " << setw(10) << cache->HIT[1] << " MISSES: " << setw(10) << cache->MISS[1] << endl;

    cout << cache->NAME;
    cout << " PREFETCH ACCESSES: " << setw(10) << cache->ACCESS[2] << " HITS: " << setw(10) << cache->HIT[2] << " MISSES: " << setw(10) << cache->MISS[2] << endl;

    cout << cache->NAME;
    cout << " WRITEBACK ACCESSES: " << setw(10) << cache->ACCESS[3] << " HITS: " << setw(10) << cache->HIT[3] << " MISSES: " << setw(10) << cache->MISS[3] << endl;


    if(cache->cache_type != 6){
    cout << cache->NAME;
    cout << " RQ ACCESS: " << setw(10) << cache->RQ[0].ACCESS_ROI << endl;

    cout << cache->NAME;
    cout << " RQ TO_CACHE: " << setw(10) << cache->RQ[0].TO_CACHE_ROI << endl;

    cout << cache->NAME;
    cout << " RQ MERGED: " << setw(10) << cache->RQ[0].MERGED_ROI << endl;

    cout << cache->NAME;
    cout << " RQ FORWARD: " << setw(10) << cache->RQ[0].FORWARD_ROI << endl;
    }else if(cache->cache_type == 6){
       for(int i=0;i< NUM_CPUS;i++){
    cout << cache->NAME;
    cout << " " << i << " RQ ACCESS: " << setw(10) << cache->RQ[i].ACCESS_ROI << endl;

    cout << cache->NAME;
    cout << " " << i << " RQ TO_CACHE: " << setw(10) << cache->RQ[i].TO_CACHE_ROI << endl;

    cout << cache->NAME;
    cout << " " << i << " RQ MERGED: " << setw(10) << cache->RQ[i].MERGED_ROI << endl;

    cout << cache->NAME;
    cout << " " << i << " RQ FORWARD: " << setw(10) << cache->RQ[i].FORWARD_ROI << endl;
       }
    }
    cout << cache->NAME;
    cout << " WQ ACCESS: " << setw(10) << cache->WQ.ACCESS_ROI << endl;

    cout << cache->NAME;
    cout << " WQ TO_CACHE: " << setw(10) << cache->WQ.TO_CACHE_ROI << endl;

    cout << cache->NAME;
    cout << " WQ MERGED: " << setw(10) << cache->WQ.MERGED_ROI << endl;

    cout << cache->NAME;
    cout << " WQ FORWARD: " << setw(10) << cache->WQ.FORWARD_ROI << endl;

}

void print_sim_stats(uint32_t cpu, CACHE *cache)
{
    uint64_t TOTAL_ACCESS = 0, TOTAL_HIT = 0, TOTAL_MISS = 0;

    for (uint32_t i=0; i<NUM_TYPES; i++) {
        TOTAL_ACCESS += cache->sim_access[cpu][i];
        TOTAL_HIT += cache->sim_hit[cpu][i];
        TOTAL_MISS += cache->sim_miss[cpu][i];
    }

    cout << cache->NAME;
    cout << " TOTAL     ACCESS: " << setw(10) << TOTAL_ACCESS << "  HIT: " << setw(10) << TOTAL_HIT << "  MISS: " << setw(10) << TOTAL_MISS << endl;

    cout << cache->NAME;
    cout << " LOAD      ACCESS: " << setw(10) << cache->sim_access[cpu][0] << "  HIT: " << setw(10) << cache->sim_hit[cpu][0] << "  MISS: " << setw(10) << cache->sim_miss[cpu][0] << endl;

    cout << cache->NAME;
    cout << " RFO       ACCESS: " << setw(10) << cache->sim_access[cpu][1] << "  HIT: " << setw(10) << cache->sim_hit[cpu][1] << "  MISS: " << setw(10) << cache->sim_miss[cpu][1] << endl;

    cout << cache->NAME;
    cout << " PREFETCH  ACCESS: " << setw(10) << cache->sim_access[cpu][2] << "  HIT: " << setw(10) << cache->sim_hit[cpu][2] << "  MISS: " << setw(10) << cache->sim_miss[cpu][2] << endl;

    cout << cache->NAME;
    cout << " WRITEBACK ACCESS: " << setw(10) << cache->sim_access[cpu][3] << "  HIT: " << setw(10) << cache->sim_hit[cpu][3] << "  MISS: " << setw(10) << cache->sim_miss[cpu][3] << endl;
}

void print_branch_stats()
{
    for (uint32_t i=0; i<NUM_CPUS; i++) {
        cout << endl << "CPU " << i << " Branch Prediction Accuracy: ";
        cout << (100.0*(ooo_cpu[i].num_branch - ooo_cpu[i].branch_mispredictions)) / ooo_cpu[i].num_branch;
        cout << "% MPKI: " << (1000.0*ooo_cpu[i].branch_mispredictions)/(ooo_cpu[i].num_retired - ooo_cpu[i].warmup_instructions) << endl;
	cout << "Number of Branches: " << ooo_cpu[i].num_branch << " Number of Mispredictions: " << ooo_cpu[i].branch_mispredictions << endl;
	cout << "Number of LOAD Instructions: " << ooo_cpu[i].num_loads << endl;
	cout << "Number of LOAD Instructions (ROI): " << ooo_cpu[i].num_loads_ROI << endl;
	cout << "Number of STORE Instructions: " << ooo_cpu[i].num_stores << endl;
	cout << "Number of STORE Instructions (ROI): " << ooo_cpu[i].num_stores_ROI << endl;
	cout << "Total Destination Memory Operands: " << ooo_cpu[i].total_dest_operands << endl;
	cout << "Total Destination Memory Operands (ROI): " << ooo_cpu[i].total_dest_operands_ROI << endl;
	cout << "Total Source Memory Operands: " << ooo_cpu[i].total_source_operands << endl;
	cout << "Total Source Memory Operands (ROI): " << ooo_cpu[i].total_source_operands_ROI << endl;
	cout << "Number of DEPENDED LOADS: " << ooo_cpu[i].DEPENDED_LOADS << endl;
	cout << "Number of DEPENDED LOADS (ROI): " << ooo_cpu[i].DEPENDED_LOADS_ROI << endl;
	cout << "Number of SQ_ADDED: " << ooo_cpu[i].SQ_ADDED << endl;
	cout << "Number of SQ_ADDED (ROI): " << ooo_cpu[i].SQ_ADDED_ROI << endl;
	cout << "Number of LQ_ADDED: " << ooo_cpu[i].LQ_ADDED << endl;
	cout << "Number of LQ_ADDED (ROI): " << ooo_cpu[i].LQ_ADDED_ROI << endl;
    }
	cout << "Number of Instructions read from trace: " << trace_reads << endl;
}

void print_dram_stats()
{
    cout << endl;
    cout << "DRAM Statistics" << endl;
    for (uint32_t i=0; i<DRAM_CHANNELS; i++) {
        cout << " CHANNEL " << i << endl;
        cout << " RQ ROW_BUFFER_HIT: " << setw(10) << uncore.DRAM.RQ[i].ROW_BUFFER_HIT << "  ROW_BUFFER_MISS: " << setw(10) << uncore.DRAM.RQ[i].ROW_BUFFER_MISS << endl;
        cout << " DBUS_CONGESTED: " << setw(10) << uncore.DRAM.dbus_congested[NUM_TYPES][NUM_TYPES] << endl; 
        cout << " WQ ROW_BUFFER_HIT: " << setw(10) << uncore.DRAM.WQ[i].ROW_BUFFER_HIT << "  ROW_BUFFER_MISS: " << setw(10) << uncore.DRAM.WQ[i].ROW_BUFFER_MISS;
        cout << "  FULL: " << setw(10) << uncore.DRAM.WQ[i].FULL << endl; 
        cout << endl;
    }

    uint64_t total_congested_cycle = 0;
    for (uint32_t i=0; i<DRAM_CHANNELS; i++)
        total_congested_cycle += uncore.DRAM.dbus_cycle_congested[i];
    cout << " AVG_CONGESTED_CYCLE: " << (total_congested_cycle / uncore.DRAM.dbus_congested[NUM_TYPES][NUM_TYPES]) << endl;
}

void reset_cache_stats(uint32_t cpu, CACHE *cache)
{
    for (uint32_t i=0; i<NUM_TYPES; i++) {
        cache->ACCESS[i] = 0;
        cache->HIT[i] = 0;
        cache->MISS[i] = 0;
        cache->MSHR_MERGED[i] = 0;
        cache->STALL[i] = 0;

        cache->sim_access[cpu][i] = 0;
        cache->sim_hit[cpu][i] = 0;
        cache->sim_miss[cpu][i] = 0;
    }

    
    cache->pf_requested = 0;
    cache->pf_issued = 0;
    cache->pf_useful = 0;
    cache->pf_useless = 0;
    cache->pf_fill = 0;

    for(int i=0;i<NUM_CPUS;i++){
    cache->RQ[i].ACCESS = 0;
    cache->RQ[i].MERGED = 0;
    cache->RQ[i].TO_CACHE = 0;
   }
    cache->WQ.ACCESS = 0;
    cache->WQ.MERGED = 0;
    cache->WQ.TO_CACHE = 0;
    cache->WQ.FORWARD = 0;
    cache->WQ.FULL = 0;
}

void finish_warmup()
{
    uint64_t elapsed_second = (uint64_t)(time(NULL) - start_time),
             elapsed_minute = elapsed_second / 60,
             elapsed_hour = elapsed_minute / 60;
    elapsed_minute -= elapsed_hour*60;
    elapsed_second -= (elapsed_hour*3600 + elapsed_minute*60);

    // reset core latency
    SCHEDULING_LATENCY = 6;
    EXEC_LATENCY = 1;
    PAGE_TABLE_LATENCY = 100;
    SWAP_LATENCY = 100000;

    cout << endl;
    for (uint32_t i=0; i<NUM_CPUS; i++) {
        cout << "Warmup complete CPU " << i << " instructions: " << ooo_cpu[i].num_retired << " cycles: " << current_core_cycle[i];
        cout << " (Simulation time: " << elapsed_hour << " hr " << elapsed_minute << " min " << elapsed_second << " sec) " << endl;

        ooo_cpu[i].begin_sim_cycle = current_core_cycle[i]; 
        ooo_cpu[i].begin_sim_instr = ooo_cpu[i].num_retired;

        // reset branch stats
        ooo_cpu[i].num_branch = 0;
        ooo_cpu[i].branch_mispredictions = 0;


	reset_cache_stats(i, &ooo_cpu[i].ITLB);
	reset_cache_stats(i, &ooo_cpu[i].DTLB);
	reset_cache_stats(i, &ooo_cpu[i].STLB);
        reset_cache_stats(i, &ooo_cpu[i].L1I);
        reset_cache_stats(i, &ooo_cpu[i].L1D);
        reset_cache_stats(i, &ooo_cpu[i].L2C);
        reset_cache_stats(i, &uncore.LLC);
    }
    cout << endl;

    // reset DRAM stats
    for (uint32_t i=0; i<DRAM_CHANNELS; i++) {
        uncore.DRAM.RQ[i].ROW_BUFFER_HIT = 0;
        uncore.DRAM.RQ[i].ROW_BUFFER_MISS = 0;
        uncore.DRAM.WQ[i].ROW_BUFFER_HIT = 0;
        uncore.DRAM.WQ[i].ROW_BUFFER_MISS = 0;
    }

    // set actual cache latency
    for (uint32_t i=0; i<NUM_CPUS; i++) {
        ooo_cpu[i].ITLB.LATENCY = ITLB_LATENCY;
        ooo_cpu[i].DTLB.LATENCY = DTLB_LATENCY;
        ooo_cpu[i].STLB.LATENCY = STLB_LATENCY;
        ooo_cpu[i].L1I.LATENCY  = L1I_LATENCY;
        ooo_cpu[i].L1D.LATENCY  = L1D_LATENCY;
        ooo_cpu[i].L2C.LATENCY  = L2C_LATENCY;
    }
    uncore.LLC.LATENCY = LLC_LATENCY;
}

void print_deadlock(uint32_t i)
{
    cout << "DEADLOCK! CPU " << i << " instr_id: " << ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].instr_id;
    cout << " translated: " << +ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].translated;
    cout << " fetched: " << +ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].fetched;
    cout << " scheduled: " << +ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].scheduled;
    cout << " executed: " << +ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].executed;
    cout << " is_memory: " << +ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].is_memory;
    cout << " event: " << ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].event_cycle;
    cout << " current: " << current_core_cycle[i] << endl;

    // print LQ entry
    cout << endl << "Load Queue Entry" << endl;
    for (uint32_t j=0; j<LQ_SIZE; j++) {
        cout << "[LQ] entry: " << j << " instr_id: " << ooo_cpu[i].LQ.entry[j].instr_id << " address: " << hex << ooo_cpu[i].LQ.entry[j].physical_address << dec << " translated: " << +ooo_cpu[i].LQ.entry[j].translated << " fetched: " << +ooo_cpu[i].LQ.entry[i].fetched << endl;
    }

    // print SQ entry
    cout << endl << "Store Queue Entry" << endl;
    for (uint32_t j=0; j<SQ_SIZE; j++) {
        cout << "[SQ] entry: " << j << " instr_id: " << ooo_cpu[i].SQ.entry[j].instr_id << " address: " << hex << ooo_cpu[i].SQ.entry[j].physical_address << dec << " translated: " << +ooo_cpu[i].SQ.entry[j].translated << " fetched: " << +ooo_cpu[i].SQ.entry[i].fetched << endl;
    }

    // print L1D MSHR entry
    PACKET_QUEUE *queue;
    queue = &ooo_cpu[i].L1D.MSHR;
    cout << endl << queue->NAME << " Entry" << endl;
    for (uint32_t j=0; j<queue->SIZE; j++) {
        cout << "[" << queue->NAME << "] entry: " << j << " instr_id: " << queue->entry[j].instr_id << " rob_index: " << queue->entry[j].rob_index;
        cout << " address: " << hex << queue->entry[j].address << " full_addr: " << queue->entry[j].full_addr << dec << " type: " << +queue->entry[j].type;
        cout << " fill_level: " << queue->entry[j].fill_level << " lq_index: " << queue->entry[j].lq_index << " sq_index: " << queue->entry[j].sq_index << endl; 
    }

    assert(0);
}

void signal_handler(int signal) 
{
	cout << "Caught signal: " << signal << endl;
	exit(1);
}

// log base 2 function from efectiu
int lg2(int n)
{
    int i, m = n, c = -1;
    for (i=0; m; i++) {
        m /= 2;
        c++;
    }
    return c;
}

uint64_t rotl64 (uint64_t n, unsigned int c)
{
    const unsigned int mask = (CHAR_BIT*sizeof(n)-1);

    assert ( (c<=mask) &&"rotate by type width or more");
    c &= mask;  // avoid undef behaviour with NDEBUG.  0 overhead for most types / compilers
    return (n<<c) | (n>>( (-c)&mask ));
}

uint64_t rotr64 (uint64_t n, unsigned int c)
{
    const unsigned int mask = (CHAR_BIT*sizeof(n)-1);

    assert ( (c<=mask) &&"rotate by type width or more");
    c &= mask;  // avoid undef behaviour with NDEBUG.  0 overhead for most types / compilers
    return (n>>c) | (n<<( (-c)&mask ));
}

RANDOM champsim_rand(champsim_seed);
// MK: Fix random generator issue
RANDOM adjacent_rand(champsim_seed+1000);
// _MK: Fix random generator issue
uint64_t va_to_pa(uint32_t cpu, uint64_t instr_id, uint64_t va, uint64_t unique_vpage)
{
#ifdef SANITY_CHECK
    if (va == 0) 
        assert(0);
#endif

    uint8_t  swap = 0;
    uint64_t high_bit_mask = rotr64(cpu, lg2(NUM_CPUS)),
             unique_va = va | high_bit_mask;
    //uint64_t vpage = unique_va >> LOG2_PAGE_SIZE,
    uint64_t vpage = unique_vpage | high_bit_mask,
             voffset = unique_va & ((1<<LOG2_PAGE_SIZE) - 1);

    // smart random number generator
    uint64_t random_ppage;

    map <uint64_t, uint64_t>::iterator pr = page_table.begin();
    map <uint64_t, uint64_t>::iterator ppage_check = inverse_table.begin();

    // check unique cache line footprint
    map <uint64_t, uint64_t>::iterator cl_check = unique_cl[cpu].find(unique_va >> LOG2_BLOCK_SIZE);
    if (cl_check == unique_cl[cpu].end()) { // we've never seen this cache line before
        unique_cl[cpu].insert(make_pair(unique_va >> LOG2_BLOCK_SIZE, 0));
        num_cl[cpu]++;
    }
    else
        cl_check->second++;

    pr = page_table.find(vpage);
    if (pr == page_table.end()) { // no VA => PA translation found 

        if (allocated_pages >= DRAM_PAGES) { // not enough memory

            // TODO: elaborate page replacement algorithm
            // here, ChampSim randomly selects a page that is not recently used and we only track 32K recently accessed pages
            uint8_t  found_NRU = 0;
            uint64_t NRU_vpage = 0; // implement it
            map <uint64_t, uint64_t>::iterator pr2 = recent_page.begin();
            for (pr = page_table.begin(); pr != page_table.end(); pr++) {

                NRU_vpage = pr->first;
                if (recent_page.find(NRU_vpage) == recent_page.end()) {
                    found_NRU = 1;
                    break;
                }
            }
#ifdef SANITY_CHECK
            if (found_NRU == 0)
                assert(0);

            if (pr == page_table.end())
                assert(0);
#endif
            DP ( if (warmup_complete[cpu]) {
            cout << "[SWAP] update page table NRU_vpage: " << hex << pr->first << " new_vpage: " << vpage << " ppage: " << pr->second << dec << endl; });

            // update page table with new VA => PA mapping
            // since we cannot change the key value already inserted in a map structure, we need to erase the old node and add a new node
            uint64_t mapped_ppage = pr->second;
            page_table.erase(pr);
            page_table.insert(make_pair(vpage, mapped_ppage));

            // update inverse table with new PA => VA mapping
            ppage_check = inverse_table.find(mapped_ppage);
#ifdef SANITY_CHECK
            if (ppage_check == inverse_table.end())
                assert(0);
#endif
            ppage_check->second = vpage;

            DP ( if (warmup_complete[cpu]) {
            cout << "[SWAP] update inverse table NRU_vpage: " << hex << NRU_vpage << " new_vpage: ";
            cout << ppage_check->second << " ppage: " << ppage_check->first << dec << endl; });

            // update page_queue
            page_queue.pop();
            page_queue.push(vpage);

            // invalidate corresponding vpage and ppage from the cache hierarchy
            ooo_cpu[cpu].ITLB.invalidate_entry(NRU_vpage);
            ooo_cpu[cpu].DTLB.invalidate_entry(NRU_vpage);
            ooo_cpu[cpu].STLB.invalidate_entry(NRU_vpage);
            for (uint32_t i=0; i<BLOCK_SIZE; i++) {
                uint64_t cl_addr = (mapped_ppage << 6) | i;
                ooo_cpu[cpu].L1I.invalidate_entry(cl_addr);
                ooo_cpu[cpu].L1D.invalidate_entry(cl_addr);
                ooo_cpu[cpu].L2C.invalidate_entry(cl_addr);
                uncore.LLC.invalidate_entry(cl_addr);
            }

            // swap complete
            swap = 1;
        } else {
            uint8_t fragmented = 0;
            if (num_adjacent_page > 0)
                random_ppage = ++previous_ppage;
            else {
                random_ppage = champsim_rand.draw_rand();
                fragmented = 1;
            }

            // encoding cpu number 
            // this allows ChampSim to run homogeneous multi-programmed workloads without VA => PA aliasing
            // (e.g., cpu0: astar  cpu1: astar  cpu2: astar  cpu3: astar...)
            //random_ppage &= (~((NUM_CPUS-1)<< (32-LOG2_PAGE_SIZE)));
            //random_ppage |= (cpu<<(32-LOG2_PAGE_SIZE)); 

            while (1) { // try to find an empty physical page number
                ppage_check = inverse_table.find(random_ppage); // check if this page can be allocated 
                if (ppage_check != inverse_table.end()) { // random_ppage is not available
                    DP ( if (warmup_complete[cpu]) {
                    cout << "vpage: " << hex << ppage_check->first << " is already mapped to ppage: " << random_ppage << dec << endl; }); 
                    
                    if (num_adjacent_page > 0)
                        fragmented = 1;

                    // try one more time
                    random_ppage = champsim_rand.draw_rand();
                    
                    // encoding cpu number 
                    //random_ppage &= (~((NUM_CPUS-1)<<(32-LOG2_PAGE_SIZE)));
                    //random_ppage |= (cpu<<(32-LOG2_PAGE_SIZE)); 
                }
                else
                    break;
            }

            // insert translation to page tables
            //printf("Insert  num_adjacent_page: %lu  vpage: %lx  ppage: %lx\n", num_adjacent_page, vpage, random_ppage);
            page_table.insert(make_pair(vpage, random_ppage));
            inverse_table.insert(make_pair(random_ppage, vpage));
            page_queue.push(vpage);
            previous_ppage = random_ppage;
            num_adjacent_page--;
            num_page[cpu]++;
            allocated_pages++;

            // try to allocate pages contiguously
            if (fragmented) {
                // MK: Fix random generator issue
                //num_adjacent_page = 1 << (rand() % 10);
                num_adjacent_page = 1 << (adjacent_rand.draw_rand() % 10);
                // _MK: Fix random generator issue
                DP ( if (warmup_complete[cpu]) {
                cout << "Recalculate num_adjacent_page: " << num_adjacent_page << endl; });
            }
        }

        if (swap)
            major_fault[cpu]++;
        else
            minor_fault[cpu]++;
    }
    else {
        //printf("Found  vpage: %lx  random_ppage: %lx\n", vpage, pr->second);
    }

    pr = page_table.find(vpage);
#ifdef SANITY_CHECK
    if (pr == page_table.end())
        assert(0);
#endif
    uint64_t ppage = pr->second;

    uint64_t pa = ppage << LOG2_PAGE_SIZE;
    pa |= voffset;

    DP ( if (warmup_complete[cpu]) {
    cout << "[PAGE_TABLE] instr_id: " << instr_id << " vpage: " << hex << vpage;
    cout << " => ppage: " << (pa >> LOG2_PAGE_SIZE) << " vadress: " << unique_va << " paddress: " << pa << dec << endl; });

    if (swap)
        stall_cycle[cpu] = current_core_cycle[cpu] + SWAP_LATENCY;
    else
        stall_cycle[cpu] = current_core_cycle[cpu] + PAGE_TABLE_LATENCY;

    //cout << "cpu: " << cpu << " allocated unique_vpage: " << hex << unique_vpage << " to ppage: " << ppage << dec << endl;

    return pa;
}

int main(int argc, char** argv)
{
	// interrupt signal hanlder
	struct sigaction sigIntHandler;
	sigIntHandler.sa_handler = signal_handler;
	sigemptyset(&sigIntHandler.sa_mask);
	sigIntHandler.sa_flags = 0;
	sigaction(SIGINT, &sigIntHandler, NULL);

    cout << endl << "*** ChampSim Multicore Out-of-Order Simulator ***" << endl << endl;

    // initialize knobs
    uint8_t show_heartbeat = 1;

    uint32_t seed_number = 0;

    // check to see if knobs changed using getopt_long()
    int c;
    while (1) {
        static struct option long_options[] =
        {
            {"warmup_instructions", required_argument, 0, 'w'},
            {"simulation_instructions", required_argument, 0, 'i'},
            {"hide_heartbeat", no_argument, 0, 'h'},
            {"cloudsuite", no_argument, 0, 'c'},
            {"low_bandwidth",  no_argument, 0, 'b'},
	    {"rrip_policies",required_argument,0,'r'},				//12 digit number encoding policy with each decimal digit BRRIP RH-RM-WH-WM-PH-PM and SRRIP RH-RM-WH-WM-PH-PM
	    {"dirty_rrip_policies",required_argument,0,'n'},
            {"psel_width",required_argument,0,'p'},
	    {"psel_mask",required_argument,0,'m'},
	    {"hit_mask",required_argument,0,'u'},
	    {"dsalgo",required_argument,0,'a'},
	    {"window_size",required_argument,0,'d'},
	    {"sr_thr",required_argument,0,'x'},
	    {"br_thr",required_argument,0,'y'},
 	    {"boost",required_argument,0,'z'},
 	    {"demote_mask",required_argument,0,'k'},
            {"track_set",required_argument,0,'s'},
	    {"traces",  no_argument, 0, 't'},
	    {"rr_cycles", required_argument, 0, 'f'},
            {0, 0, 0, 0}      
        };

        int option_index = 0;

        c = getopt_long_only(argc, argv, "wihsb", long_options, &option_index);

        // no more option characters
        if (c == -1)
            break;

        int traces_encountered = 0;

        switch(c) {
            case 'w':
                warmup_instructions = atol(optarg);
                break;
            case 'i':
                simulation_instructions = atol(optarg);
                break;
            case 'h':
                show_heartbeat = 0;
                break;
            case 'c':
                knob_cloudsuite = 1;
                MAX_INSTR_DESTINATIONS = NUM_INSTR_DESTINATIONS_SPARC;
                break;
            case 'b':
                knob_low_bandwidth = 1;
                break;
	    case 'r':
	      rrip_policies= atol(optarg);
	      break;
	    case 'n':
	      dirty_rrip_policies = atol(optarg);
	      break;
 	    case 'p':
	      psel_width= atoi(optarg);
	      break;
 	    case 'm':
	      psel_mask= atoi(optarg);
	      break;
  	    case 'u':
	      hit_mask= atoi(optarg);
	      break;
  	    case 'k':
	      demote_mask= atol(optarg);
	      break;
 	    case 's':
	      track_set= atoi(optarg);
	      break;
  	    case 'a':
	      dsalgo= atoi(optarg);
	      break;
  	    case 'd':
	      window= atoi(optarg);
	      break;
  	    case 'x':
	      sr_thr= atoi(optarg);
	      break;
 	    case 'y':
	      br_thr= atoi(optarg);
	      break;
	    case 'z':
	      boost= atoi(optarg);
	      break;
	    case 'f':
	      max_count_rr = atoi(optarg);
	      break;
           case 't':
                traces_encountered = 1;
                break;
            default:
                abort();
        }

        if (traces_encountered == 1)
            break;
    }

    // consequences of knobs
    cout << "Warmup Instructions: " << warmup_instructions << endl;
    cout << "Simulation Instructions: " << simulation_instructions << endl;
    //cout << "Scramble Loads: " << (knob_scramble_loads ? "ture" : "false") << endl;
    cout << "Number of CPUs: " << NUM_CPUS << endl;
    cout << "LLC sets: " << LLC_SET << endl;
    cout << "LLC ways: " << LLC_WAY << endl;
    cout << "Clean RRIP Policies: " << rrip_policies << " Dirty RRIP Policies: " << dirty_rrip_policies << " PSEL Width: " << psel_width << " Track Set: " << track_set << " PSEL Mask: " << psel_mask << " Demote Mask: " << demote_mask << "DS Algo: " << dsalgo << "Window size: " << window << endl;


    if (knob_low_bandwidth)
        DRAM_MTPS = 400;
    else
        DRAM_MTPS = 1600;

    // DRAM access latency
    tRP  = tRP_DRAM_CYCLE  * (CPU_FREQ / DRAM_IO_FREQ); 
    tRCD = tRCD_DRAM_CYCLE * (CPU_FREQ / DRAM_IO_FREQ); 
    tCAS = tCAS_DRAM_CYCLE * (CPU_FREQ / DRAM_IO_FREQ); 

    // default: 16 = (64 / 8) * (3200 / 1600)
    // it takes 16 CPU cycles to tranfser 64B cache block on a 8B (64-bit) bus 
    // note that dram burst length = BLOCK_SIZE/DRAM_CHANNEL_WIDTH
    DRAM_DBUS_RETURN_TIME = (BLOCK_SIZE / DRAM_CHANNEL_WIDTH) * (CPU_FREQ / DRAM_MTPS);

    printf("Off-chip DRAM Size: %u MB Channels: %u Width: %u-bit Data Rate: %u MT/s\n",
            DRAM_SIZE, DRAM_CHANNELS, 8*DRAM_CHANNEL_WIDTH, DRAM_MTPS);

    // end consequence of knobs

    // search through the argv for "-traces"
    int found_traces = 0;
    int count_traces = 0;
    char traces[NUM_CPUS][500];
    char traces_cpy[NUM_CPUS][10000];
    cout << endl;
    for (int i=0;i<argc;i++){
	if(found_traces){
	strcpy(traces[count_traces],argv[i]);
	strcpy(traces_cpy[count_traces],traces[count_traces]);
	count_traces++;
	}
	if(strcmp(argv[i],"-traces") == 0)
		found_traces=1;
    }

    if (count_traces > NUM_CPUS) {
	printf("\n*** Too many traces for the configured number of cores ***\n\n");
	assert(0);
        }
    if (count_traces != NUM_CPUS) {
        printf("\n*** Not enough traces for the configured number of cores ***\n\n");
        assert(0);
        }

    int cpus[NUM_CPUS];
    for(int i=0;i<NUM_CPUS;i++)
        cpus[i] = i;
    int f,t,len;
    char temp_string[500];
    len = NUM_CPUS;
    for(f=0;f<len;f++){
        for(t=f+1;t<len;t++){
                if(strcmp(traces[t],traces[f]) < 0){
                        strcpy(temp_string,traces[f]);
                        strcpy(traces[f],traces[t]);
                        strcpy(traces[t],temp_string);
                }
        }
    }

    for(int i=0;i<NUM_CPUS;i++){
	for(int j=0;j<NUM_CPUS;j++){
		if(strcmp(traces_cpy[i],traces[j]) == 0){
			cpus[i] = j;
		}
	}
}


    for(int i=0;i<NUM_CPUS;i++){
	printf("CPU %d runs %s\n", i, traces[i]);
    }

    cout << "NOT SORTED" << endl;
    for(int i=0;i<NUM_CPUS;i++){ 
        cout << "TRACE STRING: " << traces_cpy[i] << endl;
    }
    cout << "SORTED" << endl;
    for(int i=0;i<NUM_CPUS;i++){ 
        cout << "TRACE STRING: " << traces[i] << endl;
    }

    cout << "INITIAL" << endl;
    for(int i=0;i<NUM_CPUS;i++){
	cout << "TRACE STRING: " << traces[cpus[i]] << endl;
    }
   

    for (int i=0; i<count_traces; i++) {
        if (found_traces) {

            sprintf(ooo_cpu[i].trace_string, "%s", traces[i]);

            char *full_name = ooo_cpu[i].trace_string,
                 *last_dot = strrchr(ooo_cpu[i].trace_string, '.');

            if (full_name[last_dot - full_name + 1] == 'g') // gzip format
                sprintf(ooo_cpu[i].gunzip_command, "gunzip -c %s", traces[i]);
            else if (full_name[last_dot - full_name + 1] == 'x') // xz
                sprintf(ooo_cpu[i].gunzip_command, "xz -dc %s", traces[i]);
            else {
                cout << "ChampSim does not support traces other than gz or xz compression!" << endl; 
                assert(0);
            }

            char *pch[100];
            int count_str = 0;
            pch[0] = strtok (traces[i], " /,.-");
            while (pch[count_str] != NULL) {
                //printf ("%s %d\n", pch[count_str], count_str);
                count_str++;
                pch[count_str] = strtok (NULL, " /,.-");
            }

            //printf("max count_str: %d\n", count_str);
            //printf("application: %s\n", pch[count_str-3]);

            int j = 0;
            while (pch[count_str-3][j] != '\0') {
                seed_number += pch[count_str-3][j];
                //printf("%c %d %d\n", pch[count_str-3][j], j, seed_number);
                j++;
            }

            ooo_cpu[i].trace_file = popen(ooo_cpu[i].gunzip_command, "r");
            if (ooo_cpu[i].trace_file == NULL) {
                printf("\n*** Trace file not found: %s ***\n\n", traces[i]);
                assert(0);
            }
        }
    }
    // end trace file setup

  /*  //Sort CPUs in alphabetical order based on traces
    int cpus[NUM_CPUS], temp;
    for(int i=0;i<NUM_CPUS;i++)
	cpus[i] = i;
    int f,t,len;
    char *temp_string;
    len = NUM_CPUS;
    for(f=0;f<len;f++){
	for(t=f+1;t<len;t++){
		if(strcmp(ooo_cpu[cpus[t]].trace_string,ooo_cpu[cpus[f]].trace_string) < 0){
			strcpy(temp_string,ooo_cpu[f].trace_string);
			strcpy(ooo_cpu[f].trace_string,ooo_cpu[t].trace_string);
			strcpy(ooo_cpu[t].trace_string,temp_string);
			temp = cpus[f];
			cpus[f] = cpus[t];
			cpus[t] = temp;	
		}
	}
    }
    cout << "NOT SORTED" << endl;
    for(int i=0;i<NUM_CPUS;i++){
	cout << "TRACE STRING: " << ooo_cpu[i].trace_string << endl;
    }
    cout << "SORTED" << endl;
    for(int i=0;i<NUM_CPUS;i++){
        cout << "TRACE STRING: " << ooo_cpu[cpus[i]].trace_string << endl;
    }
*/
    // TODO: can we initialize these variables from the class constructor?
    srand(seed_number);
    champsim_seed = seed_number;
    cout << endl << "champsim_seed used: " << champsim_seed << endl << endl;
    
    for (int i=0; i<NUM_CPUS; i++) {

        ooo_cpu[i].cpu = i; 
        ooo_cpu[i].warmup_instructions = warmup_instructions;
        ooo_cpu[i].simulation_instructions = simulation_instructions;
        ooo_cpu[i].begin_sim_cycle = 0; 
        ooo_cpu[i].begin_sim_instr = warmup_instructions;

        // ROB
        ooo_cpu[i].ROB.cpu = i;

        // BRANCH PREDICTOR
        ooo_cpu[i].initialize_branch_predictor();

        // TLBs
        ooo_cpu[i].ITLB.cpu = i;
        ooo_cpu[i].ITLB.cache_type = IS_ITLB;
        ooo_cpu[i].ITLB.fill_level = FILL_L1;
        ooo_cpu[i].ITLB.extra_interface = &ooo_cpu[i].L1I;
        ooo_cpu[i].ITLB.lower_level = &ooo_cpu[i].STLB; 

        ooo_cpu[i].DTLB.cpu = i;
        ooo_cpu[i].DTLB.cache_type = IS_DTLB;
        ooo_cpu[i].DTLB.MAX_READ = (2 > MAX_READ_PER_CYCLE) ? MAX_READ_PER_CYCLE : 2;
        ooo_cpu[i].DTLB.fill_level = FILL_L1;
        ooo_cpu[i].DTLB.extra_interface = &ooo_cpu[i].L1D;
        ooo_cpu[i].DTLB.lower_level = &ooo_cpu[i].STLB;

        ooo_cpu[i].STLB.cpu = i;
        ooo_cpu[i].STLB.cache_type = IS_STLB;
        ooo_cpu[i].STLB.fill_level = FILL_L2;
        ooo_cpu[i].STLB.upper_level_icache[i] = &ooo_cpu[i].ITLB;
        ooo_cpu[i].STLB.upper_level_dcache[i] = &ooo_cpu[i].DTLB;

        // PRIVATE CACHE
        ooo_cpu[i].L1I.cpu = i;
        ooo_cpu[i].L1I.cache_type = IS_L1I;
        ooo_cpu[i].L1I.MAX_READ = (FETCH_WIDTH > MAX_READ_PER_CYCLE) ? MAX_READ_PER_CYCLE : FETCH_WIDTH;
        ooo_cpu[i].L1I.fill_level = FILL_L1;
        ooo_cpu[i].L1I.lower_level = &ooo_cpu[i].L2C; 

        ooo_cpu[i].L1D.cpu = i;
        ooo_cpu[i].L1D.cache_type = IS_L1D;
        ooo_cpu[i].L1D.MAX_READ = (2 > MAX_READ_PER_CYCLE) ? MAX_READ_PER_CYCLE : 2;
        ooo_cpu[i].L1D.fill_level = FILL_L1;
        ooo_cpu[i].L1D.lower_level = &ooo_cpu[i].L2C; 
        ooo_cpu[i].L1D.l1d_prefetcher_initialize();

        ooo_cpu[i].L2C.cpu = i;
        ooo_cpu[i].L2C.cache_type = IS_L2C;
        ooo_cpu[i].L2C.fill_level = FILL_L2;
        ooo_cpu[i].L2C.upper_level_icache[i] = &ooo_cpu[i].L1I;
        ooo_cpu[i].L2C.upper_level_dcache[i] = &ooo_cpu[i].L1D;
        ooo_cpu[i].L2C.lower_level = &uncore.LLC;
        ooo_cpu[i].L2C.l2c_prefetcher_initialize();

        // SHARED CACHE
        uncore.LLC.cache_type = IS_LLC;
        uncore.LLC.fill_level = FILL_LLC;
        uncore.LLC.upper_level_icache[i] = &ooo_cpu[i].L2C;
        uncore.LLC.upper_level_dcache[i] = &ooo_cpu[i].L2C;
        uncore.LLC.lower_level = &uncore.DRAM;

        // OFF-CHIP DRAM
        uncore.DRAM.fill_level = FILL_DRAM;
        uncore.DRAM.upper_level_icache[i] = &uncore.LLC;
        uncore.DRAM.upper_level_dcache[i] = &uncore.LLC;
        for (uint32_t i=0; i<DRAM_CHANNELS; i++) {
            uncore.DRAM.RQ[i].is_RQ = 1;
            uncore.DRAM.WQ[i].is_WQ = 1;
        }

        warmup_complete[i] = 0;
        //all_warmup_complete = NUM_CPUS;
        simulation_complete[i] = 0;
        current_core_cycle[i] = 0;
        stall_cycle[i] = 0;
        
        previous_ppage = 0;
        num_adjacent_page = 0;
        num_cl[i] = 0;
        allocated_pages = 0;
        num_page[i] = 0;
        minor_fault[i] = 0;
        major_fault[i] = 0;
    }

    uncore.LLC.llc_initialize_replacement();

    // simulation entry point
    start_time = time(NULL);
    uint8_t run_simulation = 1;
    while (run_simulation) {

        uint64_t elapsed_second = (uint64_t)(time(NULL) - start_time),
                 elapsed_minute = elapsed_second / 60,
                 elapsed_hour = elapsed_minute / 60;
        elapsed_minute -= elapsed_hour*60;
        elapsed_second -= (elapsed_hour*3600 + elapsed_minute*60);
	int i=0;
        for (int j=0; j<NUM_CPUS; j++) {
	    if(all_warmup_complete < NUM_CPUS){
		i = j;
	    }else if(all_warmup_complete >= NUM_CPUS){
		i = cpus[j];
	    }

            // proceed one cycle
            current_core_cycle[i]++;

            //cout << "Trying to process instr_id: " << ooo_cpu[i].instr_unique_id << " fetch_stall: " << +ooo_cpu[i].fetch_stall;
            //cout << " stall_cycle: " << stall_cycle[i] << " current: " << current_core_cycle[i] << endl;

            // core might be stalled due to page fault or branch misprediction
            if (stall_cycle[i] <= current_core_cycle[i]) {

                // fetch unit
                if (ooo_cpu[i].ROB.occupancy < ooo_cpu[i].ROB.SIZE) {
                    // handle branch
                    if (ooo_cpu[i].fetch_stall == 0)
                        ooo_cpu[i].handle_branch();
                }

                // fetch
                ooo_cpu[i].fetch_instruction();


                // schedule (including decode latency)
                uint32_t schedule_index = ooo_cpu[i].ROB.next_schedule;
                if ((ooo_cpu[i].ROB.entry[schedule_index].scheduled == 0) && (ooo_cpu[i].ROB.entry[schedule_index].event_cycle <= current_core_cycle[i]))
                    ooo_cpu[i].schedule_instruction();

                // execute
                ooo_cpu[i].execute_instruction();

                // memory operation
                ooo_cpu[i].schedule_memory_instruction();
                ooo_cpu[i].execute_memory_instruction();

                // complete 
                ooo_cpu[i].update_rob();

                // retire
                if ((ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].executed == COMPLETED) && (ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].event_cycle <= current_core_cycle[i]))
                    ooo_cpu[i].retire_rob();
            }

            // heartbeat information
            if (show_heartbeat && (ooo_cpu[i].num_retired >= ooo_cpu[i].next_print_instruction)) {
                float cumulative_ipc;
                if (warmup_complete[i])
                    cumulative_ipc = (1.0*(ooo_cpu[i].num_retired - ooo_cpu[i].begin_sim_instr)) / (current_core_cycle[i] - ooo_cpu[i].begin_sim_cycle);
                else
                    cumulative_ipc = (1.0*ooo_cpu[i].num_retired) / current_core_cycle[i];
                float heartbeat_ipc = (1.0*ooo_cpu[i].num_retired - ooo_cpu[i].last_sim_instr) / (current_core_cycle[i] - ooo_cpu[i].last_sim_cycle);

                cout << "Heartbeat CPU " << i << " instructions: " << ooo_cpu[i].num_retired << " cycles: " << current_core_cycle[i];
                cout << " heartbeat IPC: " << heartbeat_ipc << " cumulative IPC: " << cumulative_ipc; 
                cout << " (Simulation time: " << elapsed_hour << " hr " << elapsed_minute << " min " << elapsed_second << " sec) " << endl;
                ooo_cpu[i].next_print_instruction += STAT_PRINTING_PERIOD;

                ooo_cpu[i].last_sim_instr = ooo_cpu[i].num_retired;
                ooo_cpu[i].last_sim_cycle = current_core_cycle[i];
            }

            // check for deadlock
            if (ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].ip && (ooo_cpu[i].ROB.entry[ooo_cpu[i].ROB.head].event_cycle + DEADLOCK_CYCLE) <= current_core_cycle[i])
                print_deadlock(i);

            // check for warmup
            // warmup complete
            if ((warmup_complete[i] == 0) && (ooo_cpu[i].num_retired > warmup_instructions)) {
                warmup_complete[i] = 1;
                all_warmup_complete++;
            }
            if (all_warmup_complete == NUM_CPUS) { // this part is called only once when all cores are warmed up
                all_warmup_complete++;
                finish_warmup();
            }

            /*
            if (all_warmup_complete == 0) { 
                all_warmup_complete = 1;
                finish_warmup();
            }
            if (ooo_cpu[1].num_retired > 0)
                warmup_complete[1] = 1;
            */
            
            // simulation complete
            if ((all_warmup_complete > NUM_CPUS) && (simulation_complete[i] == 0) && (ooo_cpu[i].num_retired >= (ooo_cpu[i].begin_sim_instr + ooo_cpu[i].simulation_instructions))) {
                simulation_complete[i] = 1;
                ooo_cpu[i].finish_sim_instr = ooo_cpu[i].num_retired - ooo_cpu[i].begin_sim_instr;
                ooo_cpu[i].finish_sim_cycle = current_core_cycle[i] - ooo_cpu[i].begin_sim_cycle;

                cout << "Finished CPU " << i << " instructions: " << ooo_cpu[i].finish_sim_instr << " cycles: " << ooo_cpu[i].finish_sim_cycle;
                cout << " cumulative IPC: " << ((float) ooo_cpu[i].finish_sim_instr / ooo_cpu[i].finish_sim_cycle);
                cout << " (Simulation time: " << elapsed_hour << " hr " << elapsed_minute << " min " << elapsed_second << " sec) " << endl;

		record_roi_stats(i, &ooo_cpu[i].ITLB);
		record_roi_stats(i, &ooo_cpu[i].DTLB);
                record_roi_stats(i, &ooo_cpu[i].L1D);
                record_roi_stats(i, &ooo_cpu[i].L1I);
                record_roi_stats(i, &ooo_cpu[i].L2C);
                record_roi_stats(i, &uncore.LLC);

                all_simulation_complete++;
            }

            if (all_simulation_complete == NUM_CPUS){
		/*cout << "-------------------------------------------------------" << endl;
                for(int i=0;i<256;i++)
			if(cpu_combinations[i]!=0)
                        cout << cpu_combinations[i] << endl;*/
                run_simulation = 0;
	    }
        }

//	if(uncore.LLC.RQ.occupancy == uncore.LLC.RQ.SIZE)
//		print_RQ = 1;

	/*if(uncore.LLC.RQ.occupancy>3){
	 	cout << "READ_QUEUE[";
		if (uncore.LLC.RQ.head < uncore.LLC.RQ.tail){
			for(uint32_t i=uncore.LLC.RQ.head;i<uncore.LLC.RQ.tail;i++){
				if(uncore.LLC.RQ.entry[i].cpu!=NUM_CPUS)
				cout << uncore.LLC.RQ.entry[i].cpu << " ";
	      }
		cout << "]" << endl;
	   	}else {
			for(uint32_t i=uncore.LLC.RQ.head;i<uncore.LLC.RQ.SIZE;i++){
				if(uncore.LLC.RQ.entry[i].cpu!=NUM_CPUS)
				cout << uncore.LLC.RQ.entry[i].cpu << " ";
	    }
			for(uint32_t i=0;i<uncore.LLC.RQ.tail;i++){
				if(uncore.LLC.RQ.entry[i].cpu!=NUM_CPUS)
				cout << uncore.LLC.RQ.entry[i].cpu << " ";
	    }
		cout << "]" << endl;
	  }
	}*/

        // TODO: should it be backward?
        uncore.LLC.operate();
        uncore.DRAM.operate();
    }

#ifndef CRC2_COMPILE
    print_branch_stats();
#endif
    uint64_t elapsed_second = (uint64_t)(time(NULL) - start_time),
             elapsed_minute = elapsed_second / 60,
             elapsed_hour = elapsed_minute / 60;
    elapsed_minute -= elapsed_hour*60;
    elapsed_second -= (elapsed_hour*3600 + elapsed_minute*60);
    
    cout << endl << "ChampSim completed all CPUs" << endl;
    if (NUM_CPUS > 1) {
        cout << endl << "Total Simulation Statistics (not including warmup)" << endl;
        for (uint32_t i=0; i<NUM_CPUS; i++) {
            cout << endl << "CPU " << i << " cumulative IPC: " << (float) (ooo_cpu[i].num_retired - ooo_cpu[i].begin_sim_instr) / (current_core_cycle[i] - ooo_cpu[i].begin_sim_cycle); 
            cout << " instructions: " << ooo_cpu[i].num_retired - ooo_cpu[i].begin_sim_instr << " cycles: " << current_core_cycle[i] - ooo_cpu[i].begin_sim_cycle << endl;
#ifndef CRC2_COMPILE
	    print_sim_stats(i, &ooo_cpu[i].ITLB);
	    print_sim_stats(i, &ooo_cpu[i].DTLB);
            print_sim_stats(i, &ooo_cpu[i].L1D);
            print_sim_stats(i, &ooo_cpu[i].L1I);
            print_sim_stats(i, &ooo_cpu[i].L2C);
            ooo_cpu[i].L1D.l1d_prefetcher_final_stats();
            ooo_cpu[i].L2C.l2c_prefetcher_final_stats();
#endif
            print_sim_stats(i, &uncore.LLC);
        }
    }

    cout << endl << "Region of Interest Statistics" << endl;
    for (uint32_t i=0; i<NUM_CPUS; i++) {
        cout << endl << "CPU " << i << " cumulative IPC: " << ((float) ooo_cpu[i].finish_sim_instr / ooo_cpu[i].finish_sim_cycle); 
        cout << " instructions: " << ooo_cpu[i].finish_sim_instr << " cycles: " << ooo_cpu[i].finish_sim_cycle << endl;
#ifndef CRC2_COMPILE
	print_roi_stats(i, &ooo_cpu[i].ITLB);
	print_roi_stats(i, &ooo_cpu[i].DTLB);
        print_roi_stats(i, &ooo_cpu[i].L1D);
        print_roi_stats(i, &ooo_cpu[i].L1I);
        print_roi_stats(i, &ooo_cpu[i].L2C);
#endif
        print_roi_stats(i, &uncore.LLC);
        cout << "Major fault: " << major_fault[i] << " Minor fault: " << minor_fault[i] << endl;
    }

    for (uint32_t i=0; i<NUM_CPUS; i++) {
        ooo_cpu[i].L1D.l1d_prefetcher_final_stats();
        ooo_cpu[i].L2C.l2c_prefetcher_final_stats();
    }

#ifndef CRC2_COMPILE
    uncore.LLC.llc_replacement_final_stats();
    print_dram_stats();
#endif
    for(int i=0;i<NUM_CPUS;i++){
	cout << "LOADS RETIRED: " << ooo_cpu[i].loads_retired << endl;
	cout << "INSTR RETIRED: " << ooo_cpu[i].instr_retired << endl;
	/*for(int j=0;j<1502;j++){
		cout << "CPU " << i << " live_cycles: " << j << " frequency: " << ooo_cpu[i].loads_live_cycles[j] << endl;	
	}*/    
    }
    return 0;
}
