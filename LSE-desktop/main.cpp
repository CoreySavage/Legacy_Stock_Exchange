//
//  main.cpp
//  LSE-desktop
//
//  Created by Corey Savage on 8/5/17.
//  Copyright © 2017 Corey Savage. All rights reserved.
//

#include <iostream>
#include <string>
#include <algorithm>
#include <vector>
#include "json.hpp"
#include <sstream>
#include <fstream>
#include <math.h>
#include <iomanip>
#include <ctime>


extern "C" {
    #include "lib/lua.h"
    #include "lib/lualib.h"
    #include "lib/lauxlib.h"
}
    
using namespace std;
using json = nlohmann::json;

string SERVERNAME = "Elysium";


int get_median(vector<double>, bool);
double get_mean(vector<double>);
double get_variance(vector<double>, double);
string convert_todate(long long, int);
static void iterate_and_print(lua_State *L, int index, json &j, string keyIn, string keyName[]);

string JSON_DATA_KEY = "auctions";
string DATE = "";
string TIME = "";

int main(int argc, const char * argv[]) {
   
    //lua_State *L = lua_open();
    
    lua_State *L = luaL_newstate();
    json j;
    
    //
    // 0 = Number of auctions
    // 1 = Total Volume
    // 2 = Buyout Median Lower
    // 3 = Buyout Median Higher
    // 4 = Bid Median Lower
    // 5 = Bid Median Higher
    // 6 = Standard Deviation
    //
    string temp_categories[] = {"0", "1", "2", "3" , "4", "5", "6"};

    // Load file.
    
    int error = lua_pcall(L, 0, 0, 0);
    if(luaL_loadfile(L, "/Users/Corey/Desktop/LSE-desktop/LSE-desktop/LSE-addon.lua") || lua_pcall(L, 0, 0, 0))
    {
        
        while (error && lua_gettop(L))
        {
            std::cout << "stack = " << lua_gettop(L) << "\n";
            std::cout << "error = " << error << "\n";
            std::cout << "message = " << lua_tostring(L, -1) << "\n";
            lua_pop(L, 1);
            error = lua_pcall(L, 0, 0, 0);
        }
        //error(L, "error running function `f': %s",lua_tostring(L, -1))
        printf("Cannot run file\n");
        return 0;
    }
    // Print table contents.
    lua_getglobal(L, "lse_preupload");
    iterate_and_print(L, -1, j, "", temp_categories);
    
    
    lua_getglobal(L, "lse");
    iterate_and_print(L, -1, j, "", temp_categories);
    
    lua_getglobal(L, "lse_user");
    iterate_and_print(L, -1, j, "", temp_categories);
    
    lua_close(L);
    string filename = "LSE-addon.json";
    string file_path = "/Users/Corey/Desktop/LSE-desktop/LSE-desktop/" + filename;
    
    j["LSE"]["filename"] = filename;
    
    std::ofstream o(file_path);
    if (!o) {
        cout << "Error-------------------------------------------------" << endl;
    }
    else {
        o << std::setw(4) << j << std::endl;
        o.close();
    }
    
    
    
    return 0;
}

static void iterate_and_print(lua_State *L, int index, json &j, string keyIn, string keyName[]) {
    lua_pushvalue(L, index);
    
    lua_pushnil(L);
    int m = 0;
    int r = 0;
    vector<double> temp_buyout;
    vector<double> temp_bid;
    
    while (lua_next(L, -2)) {
        lua_pushvalue(L, -2);
        if(lua_isstring(L, -2)) {
            string value = lua_tostring(L, -2);
            if(keyIn == "Alliance" || keyIn == "Horde") {
                int auction_num = 0;
                string temp;
                //cout << lua_tostring(L, -1) << " = " << endl;
                j["LSE"]["faction"] = keyIn;
                for(int i=0;i<value.length(); i++) {
                    
                    if(value[i] == '-') {
                        //cout << "m = " << m << ", n = " << n << ", r = " << r << endl;
                        if(m == 0) {
                            auction_num = stoi(temp);
                            j[JSON_DATA_KEY][lua_tostring(L, -1)][DATE][TIME][keyName[m]] = auction_num;
                            //cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                            
                            temp_buyout.clear();
                            temp_bid.clear();
                        }
                        else if(m == 1 && stoi(temp) != auction_num) {
                            j[JSON_DATA_KEY][lua_tostring(L, -1)][DATE][TIME][keyName[m]] = stoi(temp);
                            //cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                        }
                        m++;
                        temp = "";
                    }
                    else if(value[i] == '/') {
                        temp_buyout.push_back(stoi(temp));

                        temp = "";
                    }
                    else if (value[i] == ';') {
                        temp_bid.push_back(stoi(temp));
                        
                        temp = "";
                        r++;
                    }
                    else if (i == value.length() - 1) {
                        temp += value[i];
                        temp_bid.push_back(stoi(temp));
                        
                        temp = "";
                        r++;
                    }
                    else {
                        temp += value[i];
                        
                    }
                }
                m = 2;
                r = 0;
                bool lower = true;
                bool higher = false;
                int buyout_median_low = get_median(temp_buyout, lower);
                j[JSON_DATA_KEY][lua_tostring(L, -1)][DATE][TIME][keyName[m]] = buyout_median_low;
                //cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                m++;                 // m =3
                
                int buyout_median_high = get_median(temp_buyout, higher);
                //if (buyout_median_low != buyout_median_high) {
                j[JSON_DATA_KEY][lua_tostring(L, -1)][DATE][TIME][keyName[m]] = buyout_median_high;
                    //cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                //}
                m++;                // m = 4

                int bid_median_low = get_median(temp_bid, lower);
                //if (buyout_median_low != bid_median_low) {
                j[JSON_DATA_KEY][lua_tostring(L, -1)][DATE][TIME][keyName[m]] = bid_median_low;
                    //cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                //}
                m++;                 // m = 5
                
                int bid_median_high = get_median(temp_bid, higher);
                //if (bid_median_low != bid_median_high && buyout_median_high != bid_median_high) {
                j[JSON_DATA_KEY][lua_tostring(L, -1)][DATE][TIME][keyName[m]] = bid_median_high;
                    //cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                //}
                m++;                 // m = 6
                
                
                if (auction_num > 1) {
                    double mean = get_mean(temp_buyout);
                    //
                    //if (buyout_median_low != mean) {
                    //    mean += .5;
                    //    j[JSON_DATA_KEY][DATE][lua_tostring(L, -1)][keyName[m]] = (int)mean;
                       // cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                    //}
                    //m++;                 // m = 7
                    
                    double variance = get_variance(temp_buyout, mean);
                    if (variance > 0) {
                        //j[JSON_DATA_KEY][DATE][lua_tostring(L, -1)][keyName[m]] = (long)(variance + .5);
                        //cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                        //m++;
                
                        double standard_deviation = sqrt(variance);
                        j[JSON_DATA_KEY][lua_tostring(L, -1)][DATE][TIME][keyName[m]] = (long)(standard_deviation + .5);
                        //cout << "\t" << keyName[m] << " = " << j[keyIn][lua_tostring(L, -1)][keyName[m]] << endl;
                    }
                }
                m = 0;
                
                /*
                 cout << "}" << endl << "temp_start {" << endl;
                 for (int i=0;i<total_auction;i++) {
                 cout << temp_bid_start[i] << endl;
                 }
                 cout << "}" << endl << "temp_bid {" << endl;
                 for (int i=0;i<total_auction;i++) {
                 cout << temp_bid[i] << endl;
                 }
                 */
            }
            else if (keyIn == "time") {
                string second_key(lua_tostring(L, -1));
                if (second_key.find("end")) {
                    j["LSE"]["date"] = convert_todate(lua_tointeger(L, -2), 2);
                    j["LSE"]["time"] = convert_todate(lua_tointeger(L, -2), 3);
                    DATE = j["LSE"]["date"];
                    TIME = j["LSE"]["time"];
                }
                string date = convert_todate(lua_tointeger(L, -2), 1);
                j[keyIn][lua_tostring(L, -1)] = date;
                //cout << "\t" << lua_tostring(L, -1) << " = " << date << endl;
            }
            else if (keyIn == "universal") {
                string second_key(lua_tostring(L, -2));
                if (second_key.find("api")) {
                    j["LSE"][lua_tostring(L, -1)] = lua_tostring(L, -2);
                    //cout << "\t" << lua_tostring(L, -1) << " = " << lua_tostring(L, -2) << endl;
                }
                else {
                    j["LSE"][lua_tostring(L, -1)] = lua_tointeger(L, -2);
                    //cout << "\t" << lua_tostring(L, -1) << " = " << lua_tointeger(L, -2) << endl;
                }
            }
        }
        else {

            const char *key = lua_tostring(L, -1);
            //printf("}\n\n%s = {\n", key);
            if (key == SERVERNAME) {
                j["LSE"]["server"] = key;
            }
            iterate_and_print(L, -2, j, key, keyName);
            
        }
        lua_pop(L, 2);
    }
    lua_pop(L, 1);
}

string convert_todate(long long sec, int format) {
    char epoch_time[100];
    std::time_t t = sec;
    
    if (format == 1) {
        std::strftime(epoch_time, sizeof(epoch_time), "%Y/%m/%d-%T", std::gmtime(&t));
    }
    else if (format == 2) {
        std::strftime(epoch_time, sizeof(epoch_time), "%Y/%m/%d", std::gmtime(&t));

    }
    else if (format == 3) {
        std::strftime(epoch_time, sizeof(epoch_time), "%T", std::gmtime(&t));
        
    }
    return epoch_time;
}

int get_median(vector<double> cache_data, bool get_lower) {
    
    sort(begin(cache_data), end(cache_data));
    
    if (get_lower) {
        while(!cache_data.front()) {
            for (int i=0;i<cache_data.size()-1;i++) {
                cache_data[i] = cache_data[i+1];
            }
            cache_data.pop_back();
            if (cache_data.size() == 0) {
                cache_data[0] = 0;
                break;
            }
        }
        if (cache_data.size() < 8) {
            return cache_data.front();
        }
        else if (cache_data.size() < 16) {
            return cache_data[1];
            
        }
        else {
            int quarter_data = cache_data.size() / 4;
            int after_median = (quarter_data/2) - quarter_data;
            cache_data.erase (cache_data.begin()+quarter_data+after_median,cache_data.end());
            cache_data.erase (cache_data.begin(),cache_data.end()-1);
            
            return cache_data.front();
            
        }
    }
    else {
        if (cache_data.size() < 8) {
            return cache_data.back();
        }
        else if (cache_data.size() < 16) {
            return cache_data[cache_data.size()-2];
            
        }
        else{
            int quarter_data = cache_data.size() / 4;
            int before_median = (quarter_data/2) - quarter_data;
            cache_data.erase (cache_data.begin(),cache_data.end()-quarter_data-before_median);
            cache_data.erase (cache_data.begin()+1,cache_data.end());
            
            return cache_data.back();
        }

        
    }
    
}

double get_mean(vector<double> cache_data) {
    
    double total = 0;
    
    for (int i=0; i<cache_data.size();i++) {
        total += cache_data[i];
    }
    
    return total / cache_data.size();
    
}

double get_variance(vector<double> cache_data, double mean)
{
    double sum = 0;
    double temp = 0;
    
    for (int i=0;i<cache_data.size();i++) {
        temp = pow((cache_data[i] - mean),2);
        sum += temp;
    }
    
    return sum / cache_data.size();
}








