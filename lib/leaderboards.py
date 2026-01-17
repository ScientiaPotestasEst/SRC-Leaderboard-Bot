import srcomapi
import srcomapi.datatypes as sdt
import matplotlib.pyplot as plt
import pandas as pd
import shelve

player_colors = {}

with shelve.open('./data/config') as db:
    game_name = db['game_name']
    game_choice = db['game_choice']
    make_FG = db['make_FG']
    orientation_FG = db['orientation_FG']
    defaults_FG = db['defaults_FG']
    make_IL = db['make_IL']
    orientation_IL = db['orientation_IL']
    defaults_IL = db['defaults_IL']
    make_ranking = db['make_ranking']

api = srcomapi.SpeedrunCom()
game = api.search(sdt.Game, {"name": game_name})[game_choice]

categories = [category for category in game.categories]
categories_FG = [category for category in categories if category.type == 'per-game']
categories_IL = [category for category in categories if category.type == 'per-level']
levels = [level for level in game.levels]

# ----------- Helper Functions --------------- 

def seconds_to_time_format(total_seconds):
    show_ms = game.ruleset.get('show-milliseconds', False)

    remaining_ms = int(total_seconds * 1000)
    
    s, ms = divmod(remaining_ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    units = [
        (d, 'd', 1, d > 0),
        (h, 'h', 2, d > 0 or h > 0),
        (m, 'm', 2, d > 0 or h > 0 or m > 0),
        (s, 's', 2, d > 0 or h > 0 or m > 0 or s > 0 or not show_ms),
        (ms, 'ms', 3, show_ms)
    ]

    parts = []
    for value, suffix, precision, condition in units:
        if condition:
            # For the very first unit in the string, we don't want leading zeros
            if not parts:
                parts.append(f"{value}{suffix}")
            else:
                parts.append(f"{value:0{precision}d}{suffix}")

    # Fallback for 0ms if everything else is empty
    return " ".join(parts) if parts else "0ms"


def get_leaderboard_params(category, record_index, top_count, use_defaults):
    """Handles the extraction of default variables into the params dictionary."""
    params = {'top': top_count}
    
    if not use_defaults:
        return params

    record = category.records[record_index]
    if not record.runs:
        return params

    # Extract the variable IDs from the first run's values
    run_value_ids = record.runs[0]['run'].values
    
    for var in category.variables:
        has_default = var.values.get('default') is not None
        is_active = any(var.id == val for val in run_value_ids)
        
        if is_active and has_default:
            params[f"var-{var.id}"] = var.values['default']
            
    return params

def save_df_as_image(df, filename):
    # Total figure height should scale with the total number of lines
    fig, ax = plt.subplots()
    fig.set_figwidth(15)
    # Hide the axes (the X and Y lines/ticks)
    ax.axis('off')

    # 2. Create the Table
    table = ax.table(
        cellText=df.values, 
        colLabels=df.columns, 
        cellLoc='center', 
        loc='center'
    )

    # 3. Styling the Table
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    # table.scale(1, 2)  # Stretch cells vertically for better padding
    table.auto_set_column_width(col=list(range(len(df.columns))))

    # Apply the height to each cell
    for (row, col), cell in table.get_celld().items():
        cell.set_height(0.15) # 0.05 is a base height factor

    # Color the Header and Rows
    for (row, col), cell in table.get_celld().items():
        cell.set_facecolor("none")

        if row == 0:  # Header Row
            cell.set_text_props(weight='bold', color='#ff9900') # Blue header text
        else:         # Data Rows
            cell.set_text_props(color='#3498db')
        
        # Optional: Change the border (edge) color to be more subtle
        cell.set_edgecolor('#555555')

    # 4. Save the image
    image_path = f"./data/db/{filename}"
    plt.savefig(image_path, transparent=True, bbox_inches='tight', dpi=500)
    plt.close()
    print(f"Success! Image saved as {filename}")

def update_leaderboards():
    print("Updating leaderboards...")

    # --- Full Game (FG) Logic ---
    records_FG = {}
    for category in categories_FG:
        params = get_leaderboard_params(category, 0, 3, defaults_FG)
        endpoint = f"leaderboards/{game.id}/category/{category.id}"
        records_FG[category.name] = sdt.Leaderboard(api, data=api.get(endpoint, params=params))

    # --- Individual Levels (IL) Logic ---
    records_IL = {}
    for idx, level in enumerate(levels):
        records_IL[level.name] = {}
        for category in categories_IL:
            params = get_leaderboard_params(category, idx, 1, defaults_IL)
            endpoint = f"leaderboards/{game.id}/level/{level.id}/{category.id}"
            records_IL[level.name][category.name] = sdt.Leaderboard(api, data=api.get(endpoint, params=params))

    def join_runners_name(players):
        """Joins player names with a center dot."""
        return '·'.join(p.name for p in players)

    def get_wr_cell(record):
        """Returns a formatted string of Time + Players for the WR run(s)."""
        # Filter for first place runs
        wr_runs = [r for r in record.runs if r['place'] == 1]
        
        if not wr_runs:
            return ""

        # Get the time from the first WR run
        time_str = seconds_to_time_format(wr_runs[0]['run'].times['primary_t'])
        
        # Collect all record holders (handles ties)
        holders = []
        for run_data in wr_runs:
            holders.append(join_runners_name(run_data['run'].players))
        
        # Return time followed by player names on new lines
        return f"{time_str}\n" + "\n".join(holders)

    #%% IL leaderbord
    combo = []
    if make_IL:
        IL_table = []
        for level in levels:
            times = []
            names = []
            combo = []
            for category in categories_IL:
                if records_IL[level.name][category.name].runs == []:
                    times.append("")
                    names.append("")
                    combo.append("")
                else:
                    runs = [run for run in records_IL[level.name][category.name].runs if run['place'] == 1]
                    times.append(seconds_to_time_format(runs[0]['run'].times['primary_t']))
                    record_holders = ""
                    for wr in runs:
                        runners = ""
                        for player in wr['run'].players:
                            if player == wr['run'].players[-1]:
                                runners = runners + player.name
                            else:
                                runners = runners + player.name + u'\xb7' # center dot = u'\xb7'
                        record_holders = record_holders + '\n' + runners
                    names.append(record_holders)
                    combo.append(times[categories_IL.index(category)] + names[categories_IL.index(category)])
            IL_table.append(combo)
        
        if orientation_IL == 'vertical':
            IL_headers = [' Category\\Stage '] + [' '+level.name+' ' for level in levels]
            IL_table = [list(i) for i in zip(*IL_table)]
            for category in categories_IL:
                IL_table[categories_IL.index(category)].insert(0, category.name)
        
        elif orientation_IL == 'horizontal':
            IL_headers = [' Stage\\Category '] + [('   '+category.name+'   ') for category in categories_IL]
            for level in levels:
                IL_table[levels.index(level)].insert(0, level.name)

        IL_df = pd.DataFrame(IL_table, columns=IL_headers)
        save_df_as_image(IL_df, "Individual_Levels_Leaderboard.png")

    #%% FG leaderbord

    if make_FG:
        FG_table = []
        for category in categories_FG:
            times = []
            names = []
            combo = []
            first = [run for run in records_FG[category.name].runs if run['place'] == 1]
            second = [run for run in records_FG[category.name].runs if run['place'] == 2]
            third = [run for run in records_FG[category.name].runs if run['place'] == 3]
            placements = [first, second, third]
            for rank in placements:
                if rank == []:
                    times.append("")
                    names.append("")
                    combo.append("")
                else:
                    times.append(seconds_to_time_format(rank[0]['run'].times['primary_t']))
                    record_holders = ""
                    for run in rank:
                        runners = ""
                        for player in run['run'].players:
                            if player == run['run'].players[-1]:
                                runners = runners + player.name
                            else:
                                runners = runners + player.name + u'\xb7' # center dot = u'\xb7'
                        record_holders = record_holders + '\n' + runners
                    names.append(record_holders)
                    combo.append(times[placements.index(rank)] + names[placements.index(rank)])
            FG_table.append(combo)
        
        if orientation_FG == 'vertical':
            FG_headers = [' Category\\Placement ', ' First place ', ' Second place ', ' Third place ']
            for category in categories_FG:
                FG_table[categories_FG.index(category)].insert(0, category.name)
        
        elif orientation_IL == 'horizontal':
            FG_headers = [' Placement\\Category '] + [('   '+category.name+'   ') for category in categories_FG]
            FG_table = [list(i) for i in zip(*FG_table)]
            FG_table[0].insert(0, ' 1st ')
            FG_table[1].insert(0, ' 2nd ')
            FG_table[2].insert(0, ' 3rd ')

        FG_df = pd.DataFrame(FG_table, columns=FG_headers)
        save_df_as_image(FG_df, "Full_Game_Leaderboard.png")

    #%% Ranking

    if make_ranking:
        ranking = {}

        for category in categories_FG:
            for wr in [run for run in records_FG[category.name].runs if run['place'] == 1]:
                for player in wr['run'].players:
                    if player.name not in ranking:
                        ranking[player.name] = {}
                        ranking[player.name]['Full Game'] = 0
                        ranking[player.name]['Individual Levels'] = {}
                        for c in categories_IL:
                            ranking[player.name]['Individual Levels'][c.name] = 0
                    ranking[player.name]['Full Game'] = ranking[player.name]['Full Game'] + 1

        for level in levels:
            for category in categories_IL:
                for wr in [run for run in records_IL[level.name][category.name].runs if run['place'] == 1]:
                    for player in wr['run'].players:
                        if player.name not in ranking:
                            ranking[player.name] = {}
                            ranking[player.name]['Full Game'] = 0
                            ranking[player.name]['Individual Levels'] = {}
                            for c in categories_IL:
                                ranking[player.name]['Individual Levels'][c.name] = 0
                        ranking[player.name]['Individual Levels'][category.name] = ranking[player.name]['Individual Levels'][category.name] + 1

        for runner in ranking:
            total = ranking[runner]['Full Game']
            for category in ranking[runner]['Individual Levels']:
                total = total + ranking[runner]['Individual Levels'][category]
            ranking[runner]['Total'] = total

        sorted_ranking = sorted(ranking.items(), key = lambda x: x[1]['Total'], reverse=True)


        ranking_headers = [' Rank ', ' Runner '] + [' Full Game '] + [(' '+c.name+' ') for c in categories_IL] + ['Total']

        ranking_table = []
        for rank in range(len(sorted_ranking)):
            runner = sorted_ranking[rank][0]
            rank_IL = []
            for category in categories_IL:
                rank_IL.append(sorted_ranking[rank][1]['Individual Levels'][category.name])
            if rank > 0 and sorted_ranking[rank][1]['Total'] == sorted_ranking[rank-1][1]['Total']:
                tie = [t for t in range(len(sorted_ranking)) if sorted_ranking[t][1]['Total'] == sorted_ranking[rank][1]['Total']]
                ranking_table.append([min(tie)+1] + [runner] + [sorted_ranking[rank][1]['Full Game']] + rank_IL + [sorted_ranking[rank][1]['Total']])
            else:
                ranking_table.append([rank+1] + [runner] + [sorted_ranking[rank][1]['Full Game']] + rank_IL + [sorted_ranking[rank][1]['Total']])

        ranking_df = pd.DataFrame(ranking_table, columns=ranking_headers)
        save_df_as_image(ranking_df, "Ranking_Leaderboard.png")

    #%% Confirm update

    print("Leaderboards updated")