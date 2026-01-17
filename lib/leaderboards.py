import srcomapi
import srcomapi.datatypes as sdt
from table2ascii import table2ascii, PresetStyle, Alignment
import shelve

print("Updating leaderboards...")

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

if game.ruleset['show-milliseconds'] == False:
    def convert(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days == 0 and hours == 0 and minutes == 0:
            return f'{int(seconds):01d}'+'s'
        if days == 0 and hours == 0 and minutes != 0:
            return f'{int(minutes):01d}'+'m '+f'{int(seconds):02d}'+'s'
        if days == 0 and hours != 0:
            return f'{int(hours):01d}'+'h '+f'{int(minutes):02d}'+'m '+f'{int(seconds):02d}'+'s'
        else:
            return f'{int(days):01d}'+'d '+f'{int(hours):02d}'+'h '+f'{int(minutes):02d}'+'m '+f'{int(seconds):02d}'+'s'
elif game.ruleset['show-milliseconds'] == True:
    def convert(seconds):
        seconds, milliseconds = divmod(seconds*1000, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days == 0 and hours == 0 and minutes == 0 and seconds == 0:
            return f'{int(milliseconds):01d}'+'ms'
        if days == 0 and hours == 0 and minutes == 0 and seconds != 0:
            return f'{int(seconds):01d}'+'s '+f'{int(milliseconds):03d}'+'ms'
        if days == 0 and hours == 0 and minutes != 0:
            return f'{int(minutes):01d}'+'m '+f'{int(seconds):02d}'+'s '+f'{int(milliseconds):03d}'+'ms'
        if days == 0 and hours != 0:
            return f'{int(hours):01d}'+'h '+f'{int(minutes):02d}'+'m '+f'{int(seconds):02d}'+'s '+f'{int(milliseconds):03d}'+'ms'
        else:
            return f'{int(days):01d}'+'d '+f'{int(hours):02d}'+'h '+f'{int(minutes):02d}'+'m '+f'{int(seconds):02d}'+'s '+f'{int(milliseconds):03d}'+'ms'

categories = [category for category in game.categories]
categories_FG = [category for category in categories if category.type == 'per-game']
categories_IL = [category for category in categories if category.type == 'per-level']
levels = [level for level in game.levels]

records_FG = {}     # leaderboard of Full Game runs
for category in categories_FG:
    params = {'top': 3}
    if defaults_FG and category.records[0].runs != []:     # pick out the default variables but avoid list index overflow error
        variables = [v for v in category.variables if (any(v.id == value for value in category.records[0].runs[0]['run'].values) and v.values['default'] is not None)]
        for value in variables:
            params.update({"var-{}".format(value.id): value.values['default']})
    records_FG[category.name] = sdt.Leaderboard(api, data=api.get("leaderboards/{}/category/{}".format(game.id, category.id), params=params))

records_IL = {}     # leaderboard of IL runs
for level in levels:
  records_IL[level.name] = {}    
  for category in categories_IL:
      params = {'top': 1}
      if defaults_IL and category.records[levels.index(level)].runs != []:     # pick out the default variables but avoid list index overflow error
          variables = [v for v in category.variables if (any(v.id == value for value in category.records[levels.index(level)].runs[0]['run'].values) and v.values['default'] is not None)]
          for value in variables:
              params.update({"var-{}".format(value.id): value.values['default']})
      records_IL[level.name][category.name] = sdt.Leaderboard(api, data=api.get("leaderboards/{}/level/{}/{}".format(game.id, level.id, category.id), params=params))


#%% IL leaderbord

if make_IL:
    table = []
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
                times.append(convert(runs[0]['run'].times['primary_t']))
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
        table.append(combo)
    
    if orientation_IL == 'vertical':
        headers = [' Category\\Stage '] + [' '+level.name+' ' for level in levels]
        table = [list(i) for i in zip(*table)]
        for category in categories_IL:
            table[categories_IL.index(category)].insert(0, category.name)
    
    elif orientation_IL == 'horizontal':
        headers = [' Stage\\Category '] + [('   '+category.name+'   ') for category in categories_IL]
        for level in levels:
            table[levels.index(level)].insert(0, level.name)

    output = table2ascii(
        header=headers,
        body=table,
        first_col_heading=True,
        # column_widths=[30, 30, 30, 30],
        alignments=Alignment.CENTER,
        style=PresetStyle.double_thin_box
    )

    with open('./data/db/Individual_Levels_Leaderboard.txt', 'w', encoding="utf-8") as f:
        f.write(output)


#%% FG leaderbord

if make_FG:
    table = []
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
                times.append(convert(rank[0]['run'].times['primary_t']))
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
        table.append(combo)
    
    if orientation_FG == 'vertical':
        headers = [' Category\\Placement ', ' First place ', ' Second place ', ' Third place ']
        for category in categories_FG:
            table[categories_FG.index(category)].insert(0, category.name)
    
    elif orientation_IL == 'horizontal':
        headers = [' Placement\\Category '] + [('   '+category.name+'   ') for category in categories_FG]
        table = [list(i) for i in zip(*table)]
        table[0].insert(0, ' 1st ')
        table[1].insert(0, ' 2nd ')
        table[2].insert(0, ' 3rd ')
        
    output = table2ascii(
        header=headers,
        body=table,
        first_col_heading=True,
        # column_widths=[30, 30, 30, 30],
        alignments=Alignment.CENTER,
        style=PresetStyle.double_thin_box
    )

    with open('./data/db/Full_Game_Leaderboard.txt', 'w', encoding="utf-8") as f:
        f.write(output)


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


    headers = [' Rank ', ' Runner '] + [' Full Game '] + [(' '+c.name+' ') for c in categories_IL] + ['Total']

    table = []
    for rank in range(len(sorted_ranking)):
        runner = sorted_ranking[rank][0]
        rank_IL = []
        for category in categories_IL:
            rank_IL.append(sorted_ranking[rank][1]['Individual Levels'][category.name])
        if rank > 0 and sorted_ranking[rank][1]['Total'] == sorted_ranking[rank-1][1]['Total']:
            tie = [t for t in range(len(sorted_ranking)) if sorted_ranking[t][1]['Total'] == sorted_ranking[rank][1]['Total']]
            table.append([min(tie)+1] + [runner] + [sorted_ranking[rank][1]['Full Game']] + rank_IL + [sorted_ranking[rank][1]['Total']])
        else:
            table.append([rank+1] + [runner] + [sorted_ranking[rank][1]['Full Game']] + rank_IL + [sorted_ranking[rank][1]['Total']])


    output = table2ascii(
        header=headers,
        body=table,
        first_col_heading=True,
        # column_widths=[30, 30, 30, 30],
        alignments=Alignment.CENTER,
        style=PresetStyle.double_thin_box
    )

    with open('./data/db/Ranking_Leaderboard.txt', 'w', encoding="utf-8") as f:
        f.write(output)


#%% Confirm update

print("Leaderboards updated")