# dict2txt converts the list of dictionaries into a string that can be displayed in streamlit. dict2txt can be found in utils_func
# utils_func is imported in google_func already, so no need to import here again

import flet as ft
from functions.google_func import *
from functions.websites_func import *

width_panell = 750
width_panelr = 450
panel_hspace = 30
panel_vspace = 30
panel_interspace = 20

google_cse_key = keys['google_cse_key']

def main(page: ft.Page):
    page.title = "Research Bot"
    page.scroll = 'auto'

    def do_search(e):
        if not search_bar.value: # Throw error for blank search
            search_bar.error_text = "Enter the research topic..."
            page.update()
        else:
            for i in range(1, 4):
                var_dict[f"panel{i}l_heading"].value = ""
                var_dict[f"panel{i}l_content"].value = ""
                var_dict[f"panel{i}l"].bgcolor = "#1A1C1E"
                var_dict[f"panel{i}r_heading"].value = ""
                var_dict[f"panel{i}r_content"].value = ""
                var_dict[f"panel{i}r"].bgcolor = "#1A1C1E"
            var_dict[f"panel1l_heading"].value = "Searching..."
            page.update()
            search_topic = search_bar.value
            if '/' in search_topic and '.' in search_topic: # If the search is a URL, then summarize the page
                var_dict["panel1l_heading"].value = "Summary"
                var_dict["panel1l_content"].value, page_txt = get_summarize_page(search_topic) # found in websites_func
                var_dict["panel1l"].bgcolor = '#262626'
                page.update()
                davinci_sum, curie_sum, tags = openai_summary(var_dict["panel1l_content"].value)
                var_dict["panel1l_content"].value += '\n\nOPENAI DAVINCI SUMMARY\n' + davinci_sum + '\n\nOPENAI CURIE TAGS\n' + curie_sum.replace('\n-',',')
                page.update()

                # Enhance the summary with additional information from Google - serp for keywords, people also ask, people also search for
                if tags:
                    serp, also_search, also_ask = gsearch(tags, 10)
                    var_dict["panel1r_heading"].value = "Similar Links"
                    var_dict["panel1r_content"].value = dict2txt(parse_serp(serp, search_topic), {'description':'newline'}) # found in google_func.  # Pass search topic if it's a link, so we can remove it from the Similar Google Search list, if it is present
                    var_dict["panel1r"].bgcolor = '#262626'

                    if also_ask: 
                        var_dict["panel2l_heading"].value = "Similar Questions"
                        var_dict["panel2l_content"].value = ' - ' + '\n - '.join(also_ask)
                        var_dict["panel2l"].bgcolor = '#262626'

                    if also_search:
                        var_dict["panel2r_heading"].value = "Similar Searches"
                        var_dict["panel2r_content"].value = '\n\n'.join([f"#### [{x}](https://www.google.com/search?q={x.replace(' ', '+')})" for x in also_search])
                        var_dict["panel2r"].bgcolor = '#262626'
                    page.update()

                    gnews_list = gnews(tags, 72, 5) # Get results from Google News - query, number of hours, number of results
                    webnews_list = webnews(tags, 72, ['swarajyamag.com'], 5) # Get Results From Sites That Don't usually make to the top of Google News results
                    #print(gnews_list, webnews_list)
                    if gnews_list or webnews_list: 
                        var_dict["panel3l_heading"].value = "Similar News"
                        var_dict["panel3l_content"].value = dict2txt(gnews_list, {'publisher':'inline'}) + dict2txt(webnews_list, {'publisher':'inline'})
                        #print(dict2txt(gnews_list, {'publisher':'inline'}) + dict2txt(webnews_list, {'publisher':'inline'}))
                        var_dict["panel3l"].bgcolor = '#262626'
                    page.update()

                    gbooks_list = gbooks(tags, 5) # Get results from Google Books - query, number of results
                    if gbooks_list: 
                        var_dict["panel3r_heading"].value = "From Google Books"
                        var_dict["panel3r_content"].value = dict2txt(gbooks_list, {'author':'inline'})
                        var_dict["panel3r"].bgcolor = '#262626'
                    page.update()
            
            else: # If the search is a topic, then search in books and news
                if news_check.value:
                    var_dict["panel1l_content"].value = f"{search_topic} & {news_check.value}"
                else:
                    var_dict["panel1l_content"].value = f"{search_topic}__"
                    page.update()

    
    
    # Setup page UI elements
    news_check = ft.Checkbox(label="News", value=False)
    search_bar = ft.TextField(label="Topic", width=700, suffix=ft.FilledButton("Search", on_click=do_search), on_submit=do_search) # on_click for mouse click, on_submit for enter key
    page.add(ft.Row([search_bar, news_check]))
    var_dict = {}
    for i in range(1, 3):
        var_dict[f"panel{i}l_heading"] = ft.Text("", style=ft.TextThemeStyle.DISPLAY_MEDIUM, font_family="Georgia", selectable=True)
        var_dict[f"panel{i}l_content"] = ft.Text("", size=16, selectable=True)   
        var_dict[f"panel{i}l"] = ft.Container(content=ft.Column([var_dict[f"panel{i}l_heading"], var_dict[f"panel{i}l_content"]], width=width_panell), padding=20)     
        var_dict[f"panel{i}r_heading"] = ft.Text("", style=ft.TextThemeStyle.DISPLAY_MEDIUM, font_family="Georgia", selectable=True)
        var_dict[f"panel{i}r_content"] = ft.Markdown("", selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, on_tap_link=lambda e: page.launch_url(e.data)) # Markdown as these will clickable links, for additional serp results
        var_dict[f"panel{i}r"] = ft.Container(content=ft.Column([var_dict[f"panel{i}r_heading"], var_dict[f"panel{i}r_content"]], width=width_panelr), padding=20)
    var_dict[f"panel3l_heading"] = ft.Text("", style=ft.TextThemeStyle.DISPLAY_MEDIUM, font_family="Georgia", selectable=True)
    var_dict[f"panel3l_content"] = ft.Markdown("", selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, on_tap_link=lambda e: page.launch_url(e.data)) # Markdown as these will clickable links, for additional serp results
    var_dict[f"panel3l"] = ft.Container(content=ft.Column([var_dict[f"panel3l_heading"], var_dict[f"panel3l_content"]], width=width_panell), padding=20)     
    var_dict[f"panel3r_heading"] = ft.Text("", style=ft.TextThemeStyle.DISPLAY_MEDIUM, font_family="Georgia", selectable=True)
    var_dict[f"panel3r_content"] = ft.Markdown("", selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, on_tap_link=lambda e: page.launch_url(e.data)) # Markdown as these will clickable links, for additional serp results
    var_dict[f"panel3r"] = ft.Container(content=ft.Column([var_dict[f"panel3r_heading"], var_dict[f"panel3r_content"]], width=width_panelr), padding=20)     
    var_dict["panell"] = ft.Column(spacing=panel_vspace, controls=[var_dict[x] for x in var_dict if re.fullmatch(r"panel\d?l", x)])
    var_dict["panelr"] = ft.Column(spacing=panel_vspace, controls=[var_dict[x] for x in var_dict if re.fullmatch(r"panel\d?r", x)])
    var_dict["row1"] = ft.Row(controls=[var_dict["panell"], var_dict["panelr"]], wrap=True, spacing=panel_hspace, run_spacing=panel_hspace, vertical_alignment=ft.CrossAxisAlignment.START)
        
    page.add(var_dict[f"row1"])

ft.app(target=main, port=14001, assets_dir="assets", view=ft.WEB_BROWSER, web_renderer="html", )


        


        
