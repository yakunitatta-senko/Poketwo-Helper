import os, re, csv, json, asyncio, traceback
import aiofiles, aiohttp, requests, motor.motor_asyncio
import pandas as pd
from fuzzywuzzy import fuzz
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from imports.log_imports import *
from bot.utils.mongo import *
from imports.discord_imports import *




class Pokemon_Commands:
    def __init__(self, bot):
        self.bot = bot
        self.flag_mapping = {
            "en": "🇬🇧", "fr": "🇫🇷", "es": "🇪🇸", "de": "🇩🇪", "it": "🇮🇹", "ja": "🇯🇵",
            "ko": "🇰🇷", "zh-Hans": "🇨🇳", "ru": "🇷🇺", "es-MX": "🇲🇽", "pt": "🇵🇹",
            "nl": "🇳🇱", "tr": "🇹🇷", "ar": "🇸🇦", "th": "🇹🇭", "vi": "🇻🇳", "pl": "🇵🇱",
            "sv": "🇸🇪", "da": "🇩🇰", "no": "🇳🇴", "fi": "🇫🇮", "el": "🇬🇷", "id": "🇮🇩",
            "ms": "🇲🇾", "fil": "🇵🇭", "hu": "🇭🇺", "cs": "🇨🇿", "sk": "🇸🇰", "ro": "🇷🇴",
            "uk": "🇺🇦", "hr": "🇭🇷", "bg": "🇧🇬", "et": "🇪🇪", "lv": "🇱🇻", "lt": "🇱🇹",
            "sl": "🇸🇮", "mt": "🇲🇹", "sq": "🇦🇱", "mk": "🇲🇰", "bs": "🇧🇦", "sr": "🇷🇸",
            "cy": "🇨🇾", "ga": "🇮🇪", "gd": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "kw": "🇰🇾", "br": "🇧🇷", "af": "🇿🇦",
            "xh": "🇿🇦", "zu": "🇿🇦", "tn": "🇿🇦", "st": "🇿🇦", "ss": "🇿🇦", "nr": "🇿🇦",
            "nso": "🇿🇦", "ts": "🇿🇦", "ve": "🇿🇦", "xog": "🇺🇬", "lg": "🇺🇬", "ak": "🇬🇭",
            "tw": "🇬🇭", "bm": "🇧🇫", "my": "🇲🇲", "km": "🇰🇭", "lo": "🇱🇦", "am": "🇪🇹",
            "ti": "🇪🇹", "om": "🇪🇹", "so": "🇸🇴", "sw": "🇰🇪", "rw": "🇷🇼", "yo": "🇳🇬",
            "ig": "🇳🇬", "ha": "🇳🇬", "bn": "🇧🇩", "pa": "🇮🇳", "gu": "🇮🇳", "or": "🇮🇳",
            "ta": "🇮🇳", "te": "🇮🇳", "kn": "🇮🇳", "ml": "🇮🇳", "si": "🇱🇰", "ne": "🇳🇵",
            "dz": "🇧🇹", "be": "🇧🇾", "kk": "🇰🇿", "uz": "🇺🇿", "ky": "🇰🇬"
        }
      
        self.region_mappings = {
            "Paldea": "<:Paldea:1212335178714980403>",
            "Sinnoh": "<:Sinnoh:1212335180459544607>",
            "Alola": "<:Alola:1212335185228472411>",
            "Kalos": "<:Kalos:1212335190656024608>",
            "Galar": "<:Galar:1212335192740470876>",
            "Pasio": "<:848495108667867139:1212335194628034560>",
            "Hoenn": "<:Hoenn:1212335197304004678>",
            "Unova": "<:Unova:1212335199095095306>",
            "Kanto": "<:Kanto:1212335202341363713>",
            "Johto": "<:Kanto:1212335202341363713>",
        }
       
        self.stat_name_mapping = {
            "hp": "Hp",
            "special-attack": "Sp. Atk",
            "special-defense": "Sp. Def",
        }

    async def send_pokemon_info(self, ctx, data,type, color):
        
        name = data["name"].capitalize()
        id = data["id"]
        types = [t["type"]["name"].capitalize() for t in data["types"]]
        pokemon_type_unformatted = types

        species_name = name.replace('-', ' ')
        base_url = "https://pokeapi.co/api/v2/pokemon-species/"
        
        if type == "mega":
            mega_url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}-mega"
            mega_response = requests.get(mega_url)
            if mega_response.status_code == 200:
                try:
                    mega_data = mega_response.json()
                    data_species = mega_response.json()
                except json.JSONDecodeError:
                    await ctx.send(f"Failed to parse JSON data for mega evolution of `{name}`.")
            else:
                await ctx.send(f"Mega evolution data not found for `{name}`.")
        else:
            url = f"{base_url}{name.lower()}/"
            response_species = requests.get(url)
            if response_species.status_code != 200:
                url = f"https://pokeapi.co/api/v2/pokemon-form/{name.lower()}/"
                form_response = requests.get(url)
                if form_response.status_code == 200:
                    data_species = form_response.json()
            else:
                data_species = response_species.json()

        pokemon_description = self.get_pokemon_description(id)
        region = self.get_pokemon_region(id)
        
        if type == "shiny":
            image_url = data["sprites"]["other"]["official-artwork"]["front_shiny"]
            image_thumb = data["sprites"]["versions"]["generation-v"]["black-white"]["animated"]["front_shiny"]
        elif type == "mega":
            mega_url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}-mega"
            mega_response = requests.get(mega_url)
            if mega_response.status_code == 200:
                try:
                    mega_data = mega_response.json()
                    data = mega_data
                    image_url = mega_data["sprites"]["other"]["official-artwork"]["front_default"]
                    image_thumb = mega_data["sprites"]["versions"]["generation-v"]["black-white"]["animated"]["front_default"]
                except json.JSONDecodeError:
                    await ctx.send(f"Failed to parse JSON data for mega evolution of `{name}`.")
            else:
                await ctx.send(f"Mega evolution data not found for `{name}`.")
        else:
            image_url = data["sprites"]["other"]["official-artwork"]["front_default"]
            image_thumb = data["sprites"]["versions"]["generation-v"]["black-white"]["animated"]["front_default"]

        height, weight = float(int(data["height"])) / 10, float(int(data["weight"])) / 10
        max_stat = 255

        def format_base_stats(stats, name_map, max_stat=255, bar_length=9, filled='▰', empty='▱'):
         def format_bar(value):
          filled_len = int(value / max_stat * bar_length)
          return filled * filled_len + empty * (bar_length - filled_len)
    
         return [
             f"{name_map.get(stat['stat']['name'], stat['stat']['name']).title().replace('Hp', 'Health'):<10} "
             f"{stat['base_stat']:>5} {format_bar(stat['base_stat'])}"
             for stat in stats
             ]
        
        base_stats = "\n".join(format_base_stats(data["stats"], self.stat_name_mapping))


        alternate_names = self.get_pokemon_alternate_names(data_species, species_name)
        
        if alternate_names:
            alt_names_info = {}
            for name, lang in alternate_names:
                key = name.lower()
                flag = self.flag_mapping.get(lang, None)
                if name.lower() != lang.lower() and flag is not None:
                    if key not in alt_names_info:
                        alt_names_info[key] = f"{flag} {name}"
            name_list = sorted(list(alt_names_info.values()), key=lambda x: x.split(" ")[-1])
            alt_names_str = "\n".join(name_list[:6])
        else:
            alt_names_str = "No alternate names available."

        type_chart = await self.get_type_chart()
        weaknesses, strengths = self.find_pokemon_weaknesses(data, type_chart)

        gender = self.get_pokemon_gender_ratio_display(data_species)
        rarity = self.determine_pokemon_category(data_species)

        if pokemon_description != " ":
            embed_title = f" #{id} — {species_name.title()}" if type != "shiny" else f" #{id} — ✨ {species_name.title()}"
            embed = discord.Embed(
                title=embed_title,
                description=f"\n{pokemon_description}\n",
                color=color,
            )
        else:
            embed_title = f" #{id} — {species_name.title()}" if type != "shiny" else f" #{id} — ✨ {species_name.title()}"
            embed = discord.Embed(
                title=embed_title,
                color=color,
            )

        pokemon_dex_name = embed_title
        embed.set_image(url=image_url)
        description = f"\n{pokemon_description}\n" if pokemon_description != " " else None

        
        wes = self.format_strengths_weaknesses(weaknesses, strengths)
        pokemon_type = self.format_pokemon_type(pokemon_type_unformatted)

        h_w = f"Height: {height:.2f} m\nWeight: {weight:.2f} kg"
        appearance = h_w
        
        if region:
            region = region.title()
            if region in self.region_mappings:
                region_emoji = self.region_mappings[region]
                embed.add_field(name="Region", value=f"{region_emoji} {region}", inline=True)
                region = f"{region_emoji} {region}"

        embed.add_field(name="Names", value=alt_names_str, inline=True)

        gender_differ = False
        if gender is not None:
            gender_differ = bool(gender != "♀️ Female only" or "♂️ Male only" or "Genderless")
            
        gender_info = None
        if image_thumb:
            if gender is not None and gender != "♂ 50% - ♀ 50%":
                embed.set_footer(icon_url=image_thumb, text=appearance + f"Gender: {gender}")
                gender_info = f"Gender: {gender}"
            else:
                embed.set_footer(icon_url=image_thumb, text=appearance)
        else:
            if type == "shiny":
                image_thumb = data["sprites"]["versions"]["generation-v"]["black-white"]["front_shiny"]
            else:
                image_thumb = data["sprites"]["versions"]["generation-v"]["black-white"]["front_default"]

            if image_thumb:
                if gender and rarity is not None and gender != "♂ 50% - ♀ 50%":
                    embed.set_footer(
                        icon_url=image_thumb,
                        text=f"Rarity: {rarity}\n\n{appearance}Gender: {gender}",
                    )
                    gender_info = f"Gender: {gender}"
                elif gender is not None and gender != "♂ 50% - ♀ 50%":
                    embed.set_footer(icon_url=image_thumb, text=f"{appearance}Gender: {gender}")
                    gender_info = f"Gender: {gender}"
                else:
                    embed.set_footer(icon_url=image_thumb, text=appearance)
            else:
                embed.set_footer(text=appearance)

        self.bot.add_view(Pokebuttons(alt_names_str, species_name))

        await ctx.reply(
            embed=embed,
            view=Pokebuttons(
                alt_names_str, species_name, base_stats, type, wes,
                pokemon_type, image_url, h_w, image_thumb,
                pokemon_dex_name, color, data, gender_differ, region,
                description, gender_info, self.bot
            ),
            mention_author=False,
        )

    def get_pokemon_description(self, pokemon_id, file_path="data/commands/pokemon/pokemon_description.csv"):
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row["id"] == str(pokemon_id):
                    return row["description"]
        return "Pokémon ID not found"

    def get_pokemon_region(self, pokemon_id, file_path="data/commands/pokemon/pokemon_description.csv"):
        try:
            with open(file_path, mode="r", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    if row["id"] == str(pokemon_id):
                        return row["region"]
        except (FileNotFoundError, PermissionError, Exception):
            return None
        return None

    def get_pokemon_alternate_names(self, data_species, pokemon_name):
        try:
            if data_species:
                alternate_names = [(name["name"], name["language"]["name"]) for name in data_species["names"]]
                return alternate_names
            return None
        except KeyError:
            return None

    async def get_type_chart(self, max_retries=3):
        url = "https://pokeapi.co/api/v2/type"
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            type_chart = {}
                            types_data = (await response.json())["results"]
                            for type_data in types_data:
                                type_name = type_data["name"]
                                effectiveness_url = type_data["url"]
                                async with session.get(effectiveness_url) as effectiveness_response:
                                    if effectiveness_response.status == 200:
                                        damage_relations = (await effectiveness_response.json())["damage_relations"]
                                        type_chart[type_name] = {
                                            "double_damage_to": [],
                                            "half_damage_to": [],
                                            "no_damage_to": [],
                                            "double_damage_from": [],
                                            "half_damage_from": [],
                                            "no_damage_from": [],
                                        }
                                        for key, values in damage_relations.items():
                                            for value in values:
                                                type_chart[type_name][key].append(value["name"])
                            return type_chart
            except Exception:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
        return None

    def find_pokemon_weaknesses(self, pokemon_info, type_chart):
        if pokemon_info is None:
            return None, None
        types = [t["type"]["name"] for t in pokemon_info["types"]]
        weaknesses = set()
        strengths = set()
        for pokemon_type in types:
            weaknesses.update(type_chart.get(pokemon_type, {}).get("double_damage_from", []))
            strengths.update(type_chart.get(pokemon_type, {}).get("double_damage_to", []))
        weaknesses.discard("")
        weaknesses = {weakness.capitalize() for weakness in weaknesses}
        strengths = {strength.capitalize() for strength in strengths}
        return weaknesses, strengths

    def format_strengths_weaknesses(self, weaknesses, strengths):

     header_bullet = "□"
     branch_middle = "├─"
     branch_end = "└─"
     none_text = "None"
     def format_section(title, items):
        items = list(items)
        if not items:
            return f"{header_bullet} {title}\n{branch_end} {none_text}"
        if len(items) == 1:
            return f"{header_bullet} {title}\n{branch_end} {items[0]}"
        lines = [f"{branch_middle} {item}" for item in items[:-1]]
        lines.append(f"{branch_end} {items[-1]}")
        return f"{header_bullet} {title}\n" + "\n".join(lines)

     strengths_text = format_section("Strengths", strengths)
     weaknesses_text = format_section("Weaknesses", weaknesses)

     return f"{strengths_text}\n\n{weaknesses_text}"
    
    def format_pokemon_type(self, pokemon_type_unformatted):
     # Editable formatting config
     header_bullet = "□"
     branch_middle = "├─"
     branch_end = "└─"
     none_text = "None"

     types = list(pokemon_type_unformatted)
     if not types:
        types_formatted = f"{branch_end} {none_text}"
     elif len(types) == 1:
        types_formatted = f"{branch_end} {types[0]}"
     else:
        lines = [f"{branch_middle} {t}" for t in types[:-1]]
        lines.append(f"{branch_end} {types[-1]}")
        types_formatted = "\n".join(lines)

     return f"{header_bullet} Type\n{types_formatted}\n\n"







    def get_pokemon_gender_ratio_display(self, data_species):
        try:
            gender_rate = data_species["gender_rate"]
            if gender_rate == -1:
                return "Genderless"
            elif gender_rate == 0:
                return "♂️ Male only"
            else:
                female_ratio = (8 - gender_rate) / 8
                male_ratio = gender_rate / 8
                male_percentage = int(female_ratio * 100)
                female_percentage = int(male_ratio * 100)
                if female_percentage == 100:
                    return "♀️ Female only"
                elif male_percentage == 100:
                    return "♂️ Male only"
                return f"♂ {male_percentage}% - ♀ {female_percentage}%"
        except KeyError:
            return None

    def determine_pokemon_category(self, data_species):
        try:
            if data_species:
                if data_species["is_legendary"]:
                    return "Legendary"
                elif data_species["is_mythical"]:
                    return "Mythical"
                else:
                    flavor_text_entries = data_species["flavor_text_entries"]
                    english_flavor = next(
                        (entry["flavor_text"] for entry in flavor_text_entries 
                         if entry["language"]["name"] == "en"), None)
                    if english_flavor and "ultra beast" in english_flavor.lower():
                        return "Ultra Beast"
            return None
        except KeyError:
            return None






class CustomIdSensor:
    def __init__(self):
        self.used_ids = set()

    def register(self, base: str) -> str:
        if base not in self.used_ids:
            self.used_ids.add(base)
            return base
        i = 1
        while f"{base}_{i}" in self.used_ids:
            i += 1
        new_id = f"{base}_{i}"
        self.used_ids.add(new_id)
        return new_id

class PokeSelect(discord.ui.Select):
    def __init__(self, pokemon_forms, default_image_url, alt_names, pokemon_shiny, gender, bot, selected_index=None, custom_id="Select_Pokemon_Form"):
        self.bot = bot
        self.emoji_json_path = "data/commands/pokemon/pokemon_emojis.json"
        self.pokemon_csv_path = "data/commands/pokemon/pokemon_description.csv"
        self.pokemon_api_url = "https://pokeapi.co/api/v2/pokemon/"
        self.pokemon_form_api_url = "https://pokeapi.co/api/v2/pokemon-form/"

        self.emoji_mapping = self.load_emoji_mapping()
        self.pokemon_df = pd.read_csv(self.pokemon_csv_path)

        def is_base_form(form):
            return '-' not in form["name"] or all(x not in form["name"] for x in ["mega", "gmax", "alola", "galar", "hisui", "kalos"])

        pokemon_forms.sort(key=lambda f: (not is_base_form(f), f["name"]))

        self.selected_index = selected_index if selected_index is not None else 0
        
        self.form_urls = []

        options = []
        for index, form in enumerate(pokemon_forms):
            form_name = form["name"]
            formatted_name = self.format_pokemon_name(form_name)
            pokemon_id = self.get_pokemon_id(form_name)
            description = self.get_pokemon_description(pokemon_id['id'])

            emo = Pokemon_Emojis(bot=self.bot)
            emoji = emo.call_emoji(self.emoji_mapping, pokemon_id)

            form_url = f"{self.pokemon_api_url}{form_name.lower()}"
            self.form_urls.append(form_url)

            option = discord.SelectOption(
                label=formatted_name,
                value=form_url,
                description=f"{description[:54]}..." if len(description) > 1 else None,
                emoji=emoji,
                default=(index == self.selected_index)
            )
            options.append(option)

        super().__init__(
            options=options,
            placeholder=options[0].label if options else "Select a Pokémon form",
            custom_id=custom_id,
            max_values=1,
            min_values=0
        )

        self.default_image_url = default_image_url
        self.alt_names = alt_names
        self.pokemon_type = pokemon_shiny
        self.gender = gender

        self.region_flag_mapping = RegionFlagMapping()
        self.region_mappings = self.region_flag_mapping.region_mappings
        self.flag_mapping = self.region_flag_mapping.flag_mapping

    def get_flag(self, lang):
        return self.flag_mapping.get(lang)
    
    def get_pokemon_id(self, form_name):
        url = f"{self.pokemon_api_url}{form_name.lower()}"
        response = requests.get(url)
        data = response.json()
        return {"id": data["id"], "slug": form_name.lower()}

    def format_pokemon_name(self, name):     
        special_forms = {
            "alola": "Alolan",
            "gmax": "Gigantamax",  
            "mega": "Mega",
            "galar": "Galarian",
            "hisui": "Hisuian",
            "kalos": "Kalosian",
        }

        if "-" in name:
            parts = name.split("-")
            formatted_parts = [special_forms.get(parts[1], parts[1].capitalize()), parts[0].capitalize()]
            formatted_name = " ".join(formatted_parts)
            return formatted_name
        else:
            return name.capitalize()

    def load_emoji_mapping(self):
        if os.path.exists(self.emoji_json_path):
            with open(self.emoji_json_path, "r") as f:
                return json.load(f)
        else:
            return {}

    @staticmethod
    def get_pokemon_description(pokemon_id, file_path="data/commands/pokemon/pokemon_description.csv"):
        try:
            with open(file_path, mode="r", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    if row["id"] == str(pokemon_id):
                        return row["description"]
        except FileNotFoundError:
            return "File not found"
        except PermissionError:
            return "Permission denied"
        except Exception as e:
            print(f"An error occurred: {e}")
            return f"An error occurred: {e}"
        return "Pokémon ID not found"

    @staticmethod
    def get_pokemon_region(pokemon_id, file_path="data/commands/pokemon/pokemon_description.csv"):
        try:
            with open(file_path, mode="r", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    if row["id"] == str(pokemon_id):
                        return row["region"]
        except FileNotFoundError:
            return None
        except PermissionError:
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        return None

    def get_alternate_names(self, pokemon_name):
        alternate_names = []
        form_endpoint = f"{self.pokemon_form_api_url}{pokemon_name}"
        try:
            response = requests.get(form_endpoint)
            response.raise_for_status()
            data = response.json()
            for name_data in data["names"]:
                lang = name_data["language"]["name"]
                name = name_data["name"]
                flag = self.flag_mapping.get(lang)
                if flag and name.lower() != lang.lower():
                    alternate_names.append((name, lang))
        except requests.exceptions.RequestException:
            species_endpoint = f"{self.pokemon_api_url}{pokemon_name}"
            try:
                response = requests.get(species_endpoint)
                response.raise_for_status()
                data = response.json()
                for name_data in data["names"]:
                    lang = name_data["language"]["name"]
                    name = name_data["name"]
                    flag = self.flag_mapping.get(lang)
                    if flag and name.lower() != lang.lower():
                        alternate_names.append((name, lang))
            except requests.exceptions.RequestException as e:
                print(f"Error fetching alternate names: {e}")
        return alternate_names

    async def callback(self, interaction: discord.Interaction):
        try:
            selected_form_url = self.values[0]
            await interaction.response.defer()

            if selected_form_url in self.form_urls:
                self.selected_index = self.form_urls.index(selected_form_url)

            response = requests.get(selected_form_url)
            if response.status_code != 200:
                return

            data = response.json()
            official_artwork_url = None
            if "sprites" in data and "other" in data["sprites"]:
                if "official-artwork" in data["sprites"]["other"]:
                    if self.pokemon_type == "shiny":
                        official_artwork_url = data["sprites"]["other"]["official-artwork"]["front_shiny"]
                        image_thumb = data["sprites"]["versions"]["generation-v"]["black-white"]["front_shiny"]
                    else:
                        official_artwork_url = data["sprites"]["other"]["official-artwork"]["front_default"]
                        image_thumb = data["sprites"]["versions"]["generation-v"]["black-white"]["front_default"]

            embed = interaction.message.embeds[0]
            embed.set_image(url=official_artwork_url or self.default_image_url)

            pokemon_data = requests.get(selected_form_url).json()
            if not pokemon_data:
                return

            description = self.get_pokemon_description(pokemon_data["id"])
            height, weight = float(pokemon_data["height"]) / 10, float(pokemon_data["weight"]) / 10
            footer_text = f"Height: {height:.2f} m\nWeight: {weight:.2f} kg"
            if self.gender:
                footer_text += f"\t\t{self.gender}"

            embed.title = (
                f"#{pokemon_data['id']} — ✨ {pokemon_data['name'].replace('-', ' ').title()}"
                if self.pokemon_type == "shiny"
                else f"#{pokemon_data['id']} — {pokemon_data['name'].replace('-', ' ').title()}"
            )
            embed.description = description
            embed.set_footer(icon_url=image_thumb, text=footer_text) if 'image_thumb' in locals() else embed.set_footer(text=footer_text)
            embed.clear_fields()

            region = self.get_pokemon_region(pokemon_data["id"])
            if region and region in self.region_mappings:
                emoji = self.region_mappings[region]
                embed.add_field(name="Region", value=f"{emoji} {region.title()}", inline=True)

            alt_names = self.get_alternate_names(pokemon_data["name"])
            name_flags = {
                name.lower(): f"{self.flag_mapping.get(lang, '')} {name}"
                for name, lang in alt_names if name.lower() != lang.lower()
            }
            sorted_names = sorted(name_flags.values(), key=len)
            alt_names_str = "\n".join(sorted_names[:6]) or self.alt_names
            embed.add_field(name="Names", value=alt_names_str, inline=True)

            # Update existing select options to reflect selected_index
            for idx, option in enumerate(self.options):
                option.default = (idx == self.selected_index)

            view = discord.ui.View()
            sensor = CustomIdSensor()

            # Add only this select (self) to view with consistent custom_id
            view.add_item(self)

            types = [t["type"]["name"].capitalize() for t in pokemon_data["types"]]
            pokemon_commands = Pokemon_Commands(self.bot)
            type_chart = await pokemon_commands.get_type_chart()
            weaknesses, strengths = pokemon_commands.find_pokemon_weaknesses(pokemon_data, type_chart)

            def format_base_stats(stats):
                def bar(value):
                    filled = int(value / 255 * 9)
                    return "▰" * filled + "▱" * (9 - filled)

                name_map = {"hp": "Health", "special-attack": "Sp. Atk", "special-defense": "Sp. Def"}
                return [
                    f"{name_map.get(s['stat']['name'], s['stat']['name'].title()):<10} {s['base_stat']:>5} {bar(s['base_stat'])}"
                    for s in stats
                ]

            base_stats = "\n".join(format_base_stats(pokemon_data["stats"]))
            wes = pokemon_commands.format_strengths_weaknesses(weaknesses, strengths)
            formatted_types = pokemon_commands.format_pokemon_type(types)
            h_w = f"Height: {height:.2f} m\nWeight: {weight:.2f} kg"

            species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_data['name']}/"
            species_resp = requests.get(species_url)
            gender_info = None
            gender_differ = False
            if species_resp.status_code == 200:
                species_data = species_resp.json()
                gender_info = pokemon_commands.get_pokemon_gender_ratio_display(species_data)
                gender_differ = gender_info not in ["♀️ Female only", "♂️ Male only", "Genderless"]

            buttons = Pokebuttons(
                alt_names_str=alt_names_str,
                name=pokemon_data["name"],
                base_stats=base_stats,
                type=self.pokemon_type,
                wes=wes,
                pokemon_type=formatted_types,
                image_url=official_artwork_url,
                h_w=h_w,
                image_thumb=image_thumb if 'image_thumb' in locals() else None,
                pokemon_dex_name=embed.title,
                color=embed.color,
                pokemon_data=pokemon_data,
                gender_differ=gender_differ,
                region=region,
                description=description,
                gender_info=gender_info,
                bot=self.bot
            )

            for item in buttons.children:
                if isinstance(item, discord.ui.Button):
                    base_id = getattr(item, "custom_id", item.label or "button")
                    item.custom_id = sensor.register(base_id)
                    view.add_item(item)

            await interaction.message.edit(embed=embed, view=view)

        except Exception as e:
            print(e)







class Pokebuttons(discord.ui.View):
    def __init__(
        self,
        alt_names_str=None,
        name=None,
        base_stats=None,
        type=None,
        wes=None,
        pokemon_type=None,
        image_url=None,
        h_w=None,
        image_thumb=None,
        pokemon_dex_name=None,
        color=None,
        pokemon_data=None,
        gender_differ=None,
        region=None,
        description=None,
        gender_info=None,
        bot=None
    ):
        super().__init__(timeout=None)
        self.alt_names_str = alt_names_str
        self.pokemon_name = name
        self.pokemon_shiny = type
        self.base_stats = base_stats
        self.s_and_w = wes
        self.pokemon_type = pokemon_type
        self.image_url = image_url
        self.height_and_weight = h_w
        self.image_thumb = image_thumb
        self.pokemon_dex_name = pokemon_dex_name
        self.color = color
        self.pokemon_data = pokemon_data
        self.gender_differ = gender_differ
        self.region = region
        self.description = description
        self.gender_info = gender_info
        self.bot = bot
        

        pokemon_forms = self.get_pokemon_forms()
        if pokemon_forms and len(pokemon_forms) > 1:
            self.add_item(
                PokeSelect(
                    pokemon_forms,
                    self.image_url,
                    self.alt_names_str,
                    self.pokemon_shiny,
                    self.gender_info,
                    self.bot
                )
            )

        self.POKEMON_DIR = "data/commands/pokemon"
        os.makedirs(self.POKEMON_DIR, exist_ok=True)
        self.POKEMON_IMAGES_FILE = os.path.join(
            self.POKEMON_DIR, "pokemon_images.txt"
        )
        if not os.path.exists(self.POKEMON_IMAGES_FILE):
            with open(self.POKEMON_IMAGES_FILE, "w") as file:
                file.write("")
        self.pokemon_images = self.load_pokemon_images()

        if self.check_pokemon_has_evolutions():
            self.evolves_button = discord.ui.Button(
                label="Evolutions",
                style=discord.ButtonStyle.gray,
                custom_id="Pokemon_Evolutions_Button",
                row=1
            )
            self.evolves_button.callback = self.show_evolutions_button
            self.add_item(self.evolves_button)

    def check_pokemon_has_evolutions(self):
        try:
            species_url = f"https://pokeapi.co/api/v2/pokemon-species/{self.pokemon_name.lower()}/"
            response = requests.get(species_url)
            if response.status_code != 200:
                return False
            species_data = response.json()
            evolution_chain_url = species_data.get("evolution_chain", {}).get("url")
            if not evolution_chain_url:
                return False
            
            chain_response = requests.get(evolution_chain_url)
            if chain_response.status_code != 200:
                return False
            evolution_chain_data = chain_response.json()
            chain = evolution_chain_data.get("chain")
            
            return self.has_evolutions_sync(chain)
        except Exception:
            return False

    def has_evolutions_sync(self, chain):
        queue = [chain]
        while queue:
            current = queue.pop(0)
            if current.get("evolves_to"):
                return True
            for evolution in current.get("evolves_to", []):
                queue.append(evolution)
        return False

    def get_pokemon_forms(self):
        url = f"https://pokeapi.co/api/v2/pokemon-species/{self.pokemon_name.lower()}"
        response = requests.get(url)
        if response.status_code == 200:
            forms = response.json().get("varieties", [])
            form_details = []
            for form in forms:
                form_name = form["pokemon"]["name"]
                form_url = f"https://pokeapi.co/api/v2/pokemon/{form_name.lower()}"
                form_details.append({"name": form_name, "url": form_url})
            return form_details
        return []

    def load_pokemon_images(self):
        pokemon_images = {}
        try:
            with open(self.POKEMON_IMAGES_FILE, "r") as file:
                for line in file:
                    pokemon_name, image_link = line.strip().split(":", 1)
                    pokemon_images[pokemon_name.lower()] = image_link.strip()
        except FileNotFoundError:
            print(f"Error: {self.POKEMON_IMAGES_FILE} not found")
        return pokemon_images

    async def on_button_click(self, interaction: discord.Interaction):
        selected_button_id = interaction.data["custom_id"]
        print(f"Selected button ID: {selected_button_id}")
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == selected_button_id:
                    child.style = discord.ButtonStyle.blurple
                else:
                    child.style = discord.ButtonStyle.blurple

        if selected_button_id == "Pokemon_Male_Button":
            await self.show_gender_image(interaction, "male")
        elif selected_button_id == "Pokemon_Female_Button":
            await self.show_gender_image(interaction, "female")

    async def show_gender_image(self, interaction: discord.Interaction, gender):
        if gender == "male":
            male_button = self.children[0]
            female_button = self.children[1]
        else:
            male_button = self.children[1]
            female_button = self.children[0]

        try:
            if gender == "male":
                image_url = self.pokemon_data["sprites"]["other"]["official-artwork"]["front_default"]
            else:
                pokemon_name_lower = self.pokemon_name.lower()
                if pokemon_name_lower in self.pokemon_images:
                    image_url = self.pokemon_images[pokemon_name_lower]
                else:
                    image_url = self.pokemon_images.get("front_female", None)

            embed = interaction.message.embeds[0]
            embed.set_image(url=image_url)
            await interaction.response.edit_message(embed=embed)

            male_button.style = discord.ButtonStyle.blurple
            female_button.style = discord.ButtonStyle.gray
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    async def show_evolutions_button(self, interaction: discord.Interaction):
        try:
            await self.show_evolutions(interaction)
        except requests.exceptions.RequestException as e:
            await interaction.response.send_message(
                f"Error fetching Pokémon evolution chain: {str(e)}", ephemeral=True
            )

    async def show_evolutions(self, interaction: discord.Interaction):
        try:
            evolution_chain_data = await self.get_pokemon_evolution_chain(self.pokemon_name)
            if not evolution_chain_data:
                await interaction.response.send_message(
                    f"No evolution chain found for {self.pokemon_name.title()}.", ephemeral=True
                )
                return

            embeds = await self.display_evolution_chain(evolution_chain_data)
            await interaction.response.send_message(embeds=embeds[:10], ephemeral=True)

            if len(embeds) > 10:
                await interaction.followup.send(embeds=embeds[10:], ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Error fetching Pokémon evolution chain: {str(e)}", ephemeral=True)

    @staticmethod
    async def get_pokemon_evolution_chain(pokemon_name):
        async with aiohttp.ClientSession() as session:
            species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}/"
            async with session.get(species_url) as response:
                if response.status != 200:
                    return None
                species_data = await response.json()
                evolution_chain_url = species_data.get("evolution_chain", {}).get("url")
                if not evolution_chain_url:
                    return None
            async with session.get(evolution_chain_url) as response:
                if response.status != 200:
                    return None
                evolution_chain_data = await response.json()
                return evolution_chain_data.get("chain")

    async def display_evolution_chain(self, chain):
        embeds = []
        queue = [chain]
        final_forms = set()

        while queue:
            current_chain = queue.pop(0)
            species_name = current_chain["species"]["name"].title()

            if not current_chain.get("evolves_to"):
                final_forms.add(species_name)
                continue

            for evolution in current_chain["evolves_to"]:
                details = evolution["evolution_details"][0] if evolution["evolution_details"] else {}
                next_pokemon_name = evolution["species"]["name"].title()
                method = await self.determine_evolution_method(species_name, details, next_pokemon_name)

                if method:
                    embed = await self.create_pokemon_embed(species_name, method, next_pokemon_name)
                    embeds.append(embed)

                queue.append(evolution)

        for final_form in final_forms:
            embed = await self.create_pokemon_embed(final_form, "is the final form", final_form)
            embeds.append(embed)

        return embeds

    @staticmethod
    async def determine_evolution_method(current_pokemon, evolution_details, next_pokemon):
        trigger = evolution_details.get("trigger", {}).get("name")
        item = evolution_details.get("item")
        known_move_type = evolution_details.get("known_move_type")
        time_of_day = evolution_details.get("time_of_day")
        min_level = evolution_details.get("min_level")
        min_happiness = evolution_details.get("min_happiness")
        location = evolution_details.get("location")
        method = ""

        special_evolutions = {
            ("eevee", "leafeon"): "using a Leaf Stone",
            ("eevee", "glaceon"): "using an Ice Stone"
        }

        evolution_key = (current_pokemon.lower(), next_pokemon.lower())
        if evolution_key in special_evolutions:
            return special_evolutions[evolution_key]

        if trigger == "level-up":
            if location:
                location_name = location.get("name", "").replace("-", " ").title()
                if "moss" in location_name.lower() or "eterna forest" in location_name.lower():
                    method = "using a Leaf Stone"
                elif "ice" in location_name.lower() or "snowpoint" in location_name.lower():
                    method = "using an Ice Stone"
                else:
                    method = f"when leveled up at {location_name}"
            elif known_move_type:
                method = f"when leveled up while knowing a {known_move_type['name'].replace('-', ' ').title()} move"
            else:
                method = "when leveled up"
                if time_of_day:
                    method += f" at {time_of_day.title()} time"
                if min_level:
                    method += f" starting from level {min_level}"
                if min_happiness:
                    method += " while holding a Friendship Bracelet"
        elif trigger == "use-item":
            if item:
                method = f"using a {item['name'].replace('-', ' ').title()}"
        elif trigger == "trade":
            if item:
                method = f"when traded holding a {item['name'].replace('-', ' ').title()}"
            else:
                method = "when traded"
        
        return method

    async def create_pokemon_embed(self, current_pokemon, method, next_pokemon):
        embed = discord.Embed()
        sprite_url = f"https://pokemonshowdown.com/sprites/dex/{current_pokemon.lower()}.png"
        if self.pokemon_shiny:
            sprite_url = f"https://pokemonshowdown.com/sprites/dex-shiny/{current_pokemon.lower()}.png"
        embed.set_thumbnail(url=sprite_url)
        if current_pokemon == next_pokemon:
            embed.description = f"```{current_pokemon} is the final form.```"
        else:
            embed.description = f"```{current_pokemon} evolves into {next_pokemon} {method}```"
        return embed

    @discord.ui.button(
        label="Stats", style=discord.ButtonStyle.gray, custom_id="Pokemon_Stats", row=1
    )
    async def s_and_w(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(color=self.color)
        embed.add_field(name="Base Stats", value=f"```py\n{self.base_stats}```", inline=False)
        strength_weakness = "```" + self.pokemon_type + self.s_and_w + "```"
        if self.pokemon_type != "shiny":
            image = f"https://pokemonshowdown.com/sprites/dex/{self.pokemon_name}.png"
        else:
            image = f"https://pokemonshowdown.com/sprites/dex-shiny/{self.pokemon_name}.png"
        if self.image_thumb is None:
            embed.set_footer(text=self.pokemon_dex_name)
        else:
            embed.set_footer(icon_url=self.image_thumb, text=self.pokemon_dex_name)
        #embed.set_thumbnail(url=self.image_url)
        thumbnail = self.image_url
        footer = self.image_thumb
        footer_text = self.pokemon_dex_name
        pokemon_data = self.pokemon_data
        color = self.color

        await button.response.send_message(
            embed=embed,
            view=StatsView(
                color, strength_weakness, thumbnail, footer, footer_text, pokemon_data
            ),
            ephemeral=True,
        )



class RegionFlagMapping:
    def __init__(self):
        self.region_mappings = {
            "paldea": "<:Paldea:1212335178714980403>",
            "sinnoh": "<:Sinnoh:1212335180459544607>",
            "alola": "<:Alola:1212335185228472411>",
            "kalos": "<:Kalos:1212335190656024608>",
            "galar": "<:Galar:1212335192740470876>",
            "pasio": "<:848495108667867139:1212335194628034560>",
            "hoenn": "<:Hoenn:1212335197304004678>",
            "unova": "<:Unova:1212335199095095306>",
            "kanto": "<:Kanto:1212335202341363713>",
            "johto": "<:Johto:1212335202341363713>",
        }

        self.flag_mapping = {
            "en": "🇬🇧",
            "fr": "🇫🇷",
            "es": "🇪🇸",
            "de": "🇩🇪",
            "it": "🇮🇹",
            "ja": "🇯🇵",
            "ko": "🇰🇷",
            "zh-Hans": "🇨🇳",
            "ru": "🇷🇺",
            "es-MX": "🇲🇽",
            "pt": "🇵🇹",
            "nl": "🇳🇱",
            "tr": "🇹🇷",
            "ar": "🇸🇦",
            "th": "🇹🇭",
            "vi": "🇻🇳",
            "pl": "🇵🇱",
            "sv": "🇸🇪",
            "da": "🇩🇰",
            "no": "🇳🇴",
            "fi": "🇫🇮",
            "el": "🇬🇷",
            "id": "🇮🇩",
            "ms": "🇲🇾",
            "fil": "🇵🇭",
            "hu": "🇭🇺",
            "cs": "🇨🇿",
            "sk": "🇸🇰",
            "ro": "🇷🇴",
            "uk": "🇺🇦",
            "hr": "🇭🇷",
            "bg": "🇧🇬",
            "et": "🇪🇪",
            "lv": "🇱🇻",
            "lt": "🇱🇹",
            "sl": "🇸🇮",
            "mt": "🇲🇹",
            "sq": "🇦🇱",
            "mk": "🇲🇰",
            "bs": "🇧🇦",
            "sr": "🇷🇸",
            "cy": "🇨🇾",
            "ga": "🇮🇪",
            "gd": "🏴",
            "kw": "🇰🇾",
            "br": "🇧🇷",
            "af": "🇿🇦",
            "xh": "🇿🇦",
            "zu": "🇿🇦",
            "tn": "🇿🇦",
            "st": "🇿🇦",
            "ss": "🇿🇦",
            "nr": "🇿🇦",
            "nso": "🇿🇦",
            "ts": "🇿🇦",
            "ve": "🇿🇦",
            "xog": "🇺🇬",
            "lg": "🇺🇬",
            "ak": "🇬🇭",
            "tw": "🇬🇭",
            "bm": "🇧🇫",
            "my": "🇲🇲",
            "km": "🇰🇭",
            "lo": "🇱🇦",
            "am": "🇪🇹",
            "ti": "🇪🇹",
            "om": "🇪🇹",
            "so": "🇸🇴",
            "sw": "🇰🇪",
            "rw": "🇷🇼",
            "yo": "🇳🇬",
            "ig": "🇳🇬",
            "ha": "🇳🇬",
            "bn": "🇧🇩",
            "pa": "🇮🇳",
            "gu": "🇮🇳",
            "or": "🇮🇳",
            "ta": "🇮🇳",
            "te": "🇮🇳",
            "kn": "🇮🇳",
            "ml": "🇮🇳",
            "si": "🇱🇰",
            "ne": "🇳🇵",
            "dz": "🇧🇹",
            "ti": "🇪🇷",
            "be": "🇧🇾",
            "kk": "🇰🇿",
            "uz": "🇺🇿",
            "ky": "🇰🇬",
        }

import traceback

class StatsView(discord.ui.View):
    def __init__(self, color=None, strength_weakness_text=None, thumbnail_url=None, footer=None, footer_text=None, pokemon_data=None):
        super().__init__()
        self.color = color
        self.strength_weakness_text = strength_weakness_text
        self.thumbnail_url = thumbnail_url
        self.footer = footer
        self.footer_text = footer_text
        self.pokemon_data = pokemon_data
        self.csv_path = "data/commands/pokemon/pokemon_moveset.csv"
        self.moves_api = "https://pokeapi.co/api/v2/move"
        self.pokemon_api = "https://pokeapi.co/api/v2/pokemon"
        self.semaphore = asyncio.Semaphore(10)
        self.current_page = 0
        self.moves_per_page = 9
        self.moves_data = {}

    @discord.ui.button(label="Type Details", style=discord.ButtonStyle.gray)
    async def type_details(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            embed = discord.Embed(color=self.color, description=self.strength_weakness_text)
            if self.footer:
                embed.set_footer(icon_url=self.footer, text=self.footer_text)
            else:
                embed.set_footer(text=self.footer_text)
            await button.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            tb = traceback.format_exc()
            await button.response.send_message(f"Error: {e}\n```py\n{tb}```", ephemeral=True)

    @discord.ui.button(label="Moveset", style=discord.ButtonStyle.gray)
    async def moveset(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            if self.csv_exists():
                moves = await self.get_moves_from_csv()
                if moves:
                    self.moves_data = moves
                    embed = self.create_moves_embed()
                    view = self.create_nav_view()
                    await button.response.send_message(embed=embed, view=view, ephemeral=True)
                    return

            await button.response.send_message("Downloading movesets...", ephemeral=True)
            await self.download_movesets()

            moves = await self.get_moves_from_api()
            if not moves:
                await button.followup.send(f"No moves found for {self.pokemon_data['name']}", ephemeral=True)
                return

            self.moves_data = moves
            embed = self.create_moves_embed()
            view = self.create_nav_view()
            await button.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            tb = traceback.format_exc()
            try:
                print(tb)
                await button.followup.send(f"Error: {e}\n```py\n{tb}```", ephemeral=True)
            except:
                print(tb)
                await button.response.send_message(f"Error: {e}\n```py\n{tb}```", ephemeral=True)

    def csv_exists(self):
        return os.path.exists(self.csv_path) and os.path.getsize(self.csv_path) > 0

    async def get_moves_from_csv(self):
        moves = {}
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["pokemon"].lower() == self.pokemon_data['name'].lower():
                        level = int(row.get("level", 1)) if row.get("level", "").isdigit() else 1
                        moves[level] = {
                            "name": row["name"],
                            "power": row["power"],
                            "accuracy": row["accuracy"],
                            "effect": row["effect"]
                        }
        except Exception as e:
            print(f"CSV error: {e}")
            traceback.print_exc()
        return moves

    async def get_moves_from_api(self):
        moves = {}
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                url = f"{self.pokemon_api}/{self.pokemon_data['name'].lower()}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return moves
                    data = await resp.json()

                    tasks = []
                    for move in data.get("moves", []):
                        levels = [v["level_learned_at"] for v in move["version_group_details"] if v["level_learned_at"] > 0]
                        if levels:
                            level = min(levels)
                            task = self.fetch_move_data(session, move["move"]["name"], move["move"]["url"], level)
                            tasks.append((level, task))

                    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

                    for (level, _), result in zip(tasks, results):
                        if result and not isinstance(result, Exception):
                            moves[level] = result
        except Exception as e:
            print(f"API error: {e}")
            traceback.print_exc()
        return moves

    async def fetch_move_data(self, session, name, url, level):
        try:
            async with self.semaphore:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    effect = next((e["short_effect"] for e in data.get("effect_entries", []) if e["language"]["name"] == "en"), "")
                    return {
                        "name": name,
                        "power": data.get("power", ""),
                        "accuracy": data.get("accuracy", ""),
                        "effect": effect
                    }
        except Exception:
            traceback.print_exc()
            return None

    def create_moves_embed(self):
        if not self.moves_data:
            return discord.Embed(title="No moves found", color=self.color)

        sorted_levels = sorted(self.moves_data.keys())
        start = self.current_page * self.moves_per_page
        end = start + self.moves_per_page
        page_levels = sorted_levels[start:end]

        embed = discord.Embed(
            title=f"{self.pokemon_data['name'].title().replace('-', ' ')} Moveset",
            color=self.color
        )

        for level in page_levels:
            move = self.moves_data[level]
            effect = move['effect'][:97] + "..." if len(move['effect']) > 100 else move['effect']
            embed.add_field(
                name=f"{move['name'].title().replace('-', ' ')} (Lv. {level})",
                value=f"Power: {move['power'] or '—'} | Accuracy: {move['accuracy'] or '—'}\n{effect or 'No description'}",
                inline=False
            )

        total_pages = (len(self.moves_data) + self.moves_per_page - 1) // self.moves_per_page
        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages} | {len(self.moves_data)} moves")
        if self.thumbnail_url:
            embed.set_thumbnail(url=self.thumbnail_url)

        return embed

    def create_nav_view(self):
        view = discord.ui.View(timeout=300)
        total_pages = (len(self.moves_data) + self.moves_per_page - 1) // self.moves_per_page

        first = discord.ui.Button(label="<<", style=discord.ButtonStyle.secondary, disabled=self.current_page == 0, row=1)
        prev = discord.ui.Button(label="<", style=discord.ButtonStyle.secondary, disabled=self.current_page == 0)
        page = discord.ui.Button(label=f"{self.current_page + 1}/{total_pages}", style=discord.ButtonStyle.primary, disabled=True)
        next_btn = discord.ui.Button(label=">", style=discord.ButtonStyle.secondary, disabled=self.current_page >= total_pages - 1)
        last = discord.ui.Button(label=">>", style=discord.ButtonStyle.secondary, disabled=self.current_page >= total_pages - 1, row=1)

        first.callback = self.first_page
        prev.callback = self.prev_page
        next_btn.callback = self.next_page
        last.callback = self.last_page

        #view.add_item(first)
        view.add_item(prev)
        view.add_item(page)
        view.add_item(next_btn)
        #view.add_item(last)

        return view

    async def first_page(self, interaction: discord.Interaction):
        self.current_page = 0
        await self.update_page(interaction)

    async def prev_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_page(interaction)

    async def next_page(self, interaction: discord.Interaction):
        total_pages = (len(self.moves_data) + self.moves_per_page - 1) // self.moves_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
        await self.update_page(interaction)

    async def last_page(self, interaction: discord.Interaction):
        total_pages = (len(self.moves_data) + self.moves_per_page - 1) // self.moves_per_page
        self.current_page = total_pages - 1
        await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        try:
            embed = self.create_moves_embed()
            view = self.create_nav_view()
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            tb = traceback.format_exc()
            await interaction.response.send_message(f"Error: {e}\n```py\n{tb}```", ephemeral=True)

    async def download_movesets(self):
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        pokemon_names = await self.fetch_pokemon_names()

        all_moves = []
        connector = aiohttp.TCPConnector(limit=20)
        async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=300)) as session:
            for i in range(0, len(pokemon_names), 50):
                batch = pokemon_names[i:i + 50]
                tasks = [self.fetch_pokemon_moves(session, name) for name in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, list):
                        all_moves.extend(result)
                await asyncio.sleep(1)

        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            if all_moves:
                writer = csv.DictWriter(f, fieldnames=["pokemon", "name", "power", "accuracy", "effect", "level"])
                writer.writeheader()
                writer.writerows(all_moves)

    async def fetch_pokemon_names(self):
        names = []
        url = self.pokemon_api
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            while url:
                try:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            break
                        data = await resp.json()
                        names.extend([p["name"] for p in data["results"]])
                        url = data.get("next")
                except Exception:
                    traceback.print_exc()
                    break
        return names

    async def fetch_pokemon_moves(self, session, pokemon_name):
        try:
            async with self.semaphore:
                url = f"{self.pokemon_api}/{pokemon_name}"
                async with session.get(url, timeout=15) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()

                    moves = []
                    for move in data.get("moves", []):
                        levels = [v["level_learned_at"] for v in move["version_group_details"] if v["level_learned_at"] > 0]
                        if levels:
                            level = min(levels)
                            move_data = await self.fetch_move_data(session, move["move"]["name"], move["move"]["url"], level)
                            if move_data:
                                moves.append({
                                    "pokemon": pokemon_name,
                                    "name": move_data["name"],
                                    "power": move_data["power"],
                                    "accuracy": move_data["accuracy"],
                                    "effect": move_data["effect"],
                                    "level": level
                                })
                    return moves
        except Exception:
            traceback.print_exc()
            return []




####################################






























































import os, re, csv, json, asyncio, multiprocessing as mp, csv, difflib, time
from imports.log_imports import *
from functools import partial
from tqdm import tqdm, asyncio as async_tqdm
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from fuzzywuzzy import fuzz
from motor.motor_asyncio import AsyncIOMotorClient

from imports.discord_imports import *
from data.local.const import *
from bot.token import use_test_bot as ut, prefix
from bot.utils.mongo import *
from discord.ext.commands import CheckFailure, MissingRequiredArgument





   
        
             
class PoketwoSpecialPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo = MongoHelper(
            AsyncIOMotorClient(os.getenv("MONGO_URI"))["Commands"]["pokemon"]
        )

        # Define app_commands group
        self.poketwo_group = app_commands.Group(
            name="poketwo", description="Pokétwo command group"
        )
        self.poketwo_group.add_command(self.specialping)

    async def get_config(self, guild_id: int) -> dict:
        """Fetch the server config from MongoDB."""
        collection = self.mongo.get_collection("server_config")
        return await collection.find_one({"guild_id": guild_id}) or {}

    @app_commands.command(
        name="specialping",
        description="Set or view the role to ping for rare/regional Pokémon."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        role="Role to ping for special Pokémon (optional, leave empty to remove)."
    )
    async def specialping(
        self,
        interaction: discord.Interaction,
        role: discord.Role | None = None
    ):
        try:
            guild_id = interaction.guild.id
            config = await self.get_config(guild_id)
            message = "Current configuration from database:"

            # Update role if provided
            if role:
                config["special_role"] = role.id
                message = f"Special Pokémon role set to {role.mention}."
            elif "special_role" in config:
                config.pop("special_role")
                message = "Special Pokémon role removed."

            # Save config
            collection = self.mongo.get_collection("server_config")
            await collection.update_one({"guild_id": guild_id}, {"$set": config}, upsert=True)

            # Get role object for display
            special_role = interaction.guild.get_role(config.get("special_role"))

            # Build embed
            embed = discord.Embed(
                title="Pokétwo Special Ping Role",
                description=message,
                color=discord.Color.green() if role else discord.Color.blurple()
            )
            embed.set_thumbnail(
                url=interaction.guild.icon.url if interaction.guild.icon else interaction.user.display_avatar.url
            )
            embed.add_field(
                name="Current Role",
                value=f"{special_role.mention if special_role else '-'}",
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except app_commands.MissingPermissions:
            await interaction.response.send_message(
                "❌ You can't use this command. Manage Server permission required.",
                ephemeral=True
            )

        except Exception as e:
            print(f"❌ | SpecialPing Error | Guild ID: {interaction.guild.id} | {e}")
            traceback.print_exc()
            await interaction.response.send_message(
                f"❌ An unexpected error occurred: {e}", ephemeral=True
            )

        
class Pokemon_Emojis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GUILD_IDS = ["1216270817101611058","1216270002127114340","1216269922263371876","1340447626105065585", "1340447685685153852", "1340447747974762556", "1340447749111545998", "1340447923548459133", "1340447977340145717", "1340448026740916338", "1340448028196212807", "1340448148866469971", "1340448241069723749", "1340448280966074519", "1340448379729346560", "1340448496100053055", "1340448546603667619", "1340448595052335104", "1340448664157687830", "1340448723603296300", "1340448725314703390", "1340448849281548363", "1340449016089153598", "1340449082971390033", "1340449185933299723", "1340449231194030121", "1340449271366815806", "1340449391533625398", "1340449491765166231", "1340449540175691847", "1340698929922183300", "1340699061992558665", "1340699001011437610"]
        self.POKEMON_IMAGES_FOLDER = "data/commands/pokemon/pokemon_emojis"
        self.IMAGE_SOURCES = ["https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{}.png", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{}.png", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/{}.png"]
        self.emoji_json_path = "data/commands/pokemon/pokemon_emojis.json"
        self.owner_id = [1124389055598170182, 1320515815270907957]
        self.failed_downloads = set()
        self.emoji_mapping = self.load_emoji_mapping()
        os.makedirs(os.path.dirname(self.emoji_json_path), exist_ok=True)
        os.makedirs(self.POKEMON_IMAGES_FOLDER, exist_ok=True)


    def get_server_emoji_limit(self, guild):
        if guild.premium_tier >= 2:
            return 512 * 1024
        else:
            return 256 * 1024

    def resize_image_for_discord(self, image_data, guild=None):
        try:
            max_size_bytes = self.get_server_emoji_limit(guild) if guild else 256 * 1024
            img = Image.open(io.BytesIO(image_data))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            max_dimension = 128
            quality = 95
            while max_dimension >= 32:
                img_resized = img.copy()
                img_resized.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                for current_quality in range(quality, 50, -5):
                    output = io.BytesIO()
                    img_resized.save(output, format='PNG', optimize=True, compress_level=9)
                    output_size = output.tell()
                    self.logger.debug(f"Resized to {max_dimension}x{max_dimension}, size: {output_size} bytes (limit: {max_size_bytes})")
                    if output_size <= max_size_bytes:
                        output.seek(0)
                        return output.read()
                max_dimension = int(max_dimension * 0.8)
            img_minimal = img.copy()
            img_minimal.thumbnail((32, 32), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img_minimal.save(output, format='PNG', optimize=True, compress_level=9)
            output.seek(0)
            final_size = output.tell()
            self.logger.warning(f"Had to reduce image to minimal size: {final_size} bytes")
            output.seek(0)
            return output.read()
        except Exception as e:
            self.logger.error(f"Error resizing image: {e}")
            return None

    def validate_image_size(self, image_data, guild=None):
        if not image_data:
            return False, "No image data"
        max_size = self.get_server_emoji_limit(guild) if guild else 256 * 1024
        actual_size = len(image_data)
        if actual_size > max_size:
            return False, f"Image too large: {actual_size} bytes (limit: {max_size} bytes)"
        return True, "OK"

    def load_emoji_mapping(self):
        if os.path.exists(self.emoji_json_path):
            with open(self.emoji_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_pokemon_id(self, filename):
        return filename.split(".")[0].zfill(3)

    async def get_server_emoji_counts(self):
        self.logger.info("Fetching server emoji counts...")
        tasks = []
        for guild_id in self.GUILD_IDS:
            guild = self.bot.get_guild(int(guild_id))
            if guild and guild.me.guild_permissions.manage_emojis:
                tasks.append(self._get_single_server_count(guild, guild_id))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        counts = {r[0]: r[1] for r in results if not isinstance(r, Exception)}
        self.logger.info(f"Found {len(counts)} available servers")
        return counts

    async def _get_single_server_count(self, guild, guild_id):
        emoji_count = len(guild.emojis)
        max_emojis = 50 + (guild.premium_tier * 50)
        return guild_id, {'current': emoji_count, 'max': max_emojis, 'available': max_emojis - emoji_count, 'guild': guild}

    async def find_available_servers(self, min_slots=1):
        server_counts = await self.get_server_emoji_counts()
        available = [info['guild'] for info in server_counts.values() if info['available'] >= min_slots]
        self.logger.info(f"Found {len(available)} servers with {min_slots}+ available slots")
        return available

    async def download_pokemon_images(self):
        self.logger.info("Starting Pokemon image download process...")
        pokemon_ids = await self.fetch_all_pokemon_ids()
        existing_images = set(self.load_images())
        missing_pokemon_ids = [pid for pid in pokemon_ids if f"{str(pid).zfill(3)}.png" not in existing_images and pid not in self.failed_downloads]
        if not missing_pokemon_ids:
            self.logger.info("No missing images to download")
            return
        self.logger.info(f"Downloading {len(missing_pokemon_ids)} missing Pokemon images")
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            semaphore = asyncio.Semaphore(50)
            tasks = [self._download_with_semaphore(semaphore, session, pid) for pid in missing_pokemon_ids]
            results = []
            batch_size = 100
            for batch_start in range(0, len(tasks), batch_size):
                batch = tasks[batch_start:batch_start + batch_size]
                self.logger.info(f"Processing download batch {batch_start//batch_size + 1}/{(len(tasks) + batch_size - 1)//batch_size}")
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                results.extend(batch_results)
                await asyncio.sleep(0.1)
        successful = sum(1 for r in results if r is True)
        self.logger.info(f"Download complete: {successful}/{len(missing_pokemon_ids)} successful")

    async def _download_with_semaphore(self, semaphore, session, pokemon_id):
        async with semaphore:
            success = await self.download_single_image(session, pokemon_id)
            if not success:
                self.failed_downloads.add(pokemon_id)
                self.logger.warning(f"Failed to download Pokemon ID {pokemon_id}")
            return success

    async def download_single_image(self, session, pokemon_id):
        img_path = os.path.join(self.POKEMON_IMAGES_FOLDER, f"{str(pokemon_id).zfill(3)}.png")
        for source_url_template in self.IMAGE_SOURCES:
            img_url = source_url_template.format(pokemon_id)
            try:
                async with session.get(img_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        resized_content = await asyncio.get_event_loop().run_in_executor(None, self.resize_image_for_discord, content, None)
                        if resized_content:
                            is_valid, message = self.validate_image_size(resized_content)
                            if is_valid:
                                await asyncio.get_event_loop().run_in_executor(None, self._write_image_file, img_path, resized_content)
                                self.logger.debug(f"Successfully downloaded and resized Pokemon {pokemon_id}")
                                return True
                            else:
                                self.logger.error(f"Image validation failed for Pokemon {pokemon_id}: {message}")
                        else:
                            self.logger.error(f"Failed to resize image for Pokemon {pokemon_id}")
            except Exception as e:
                self.logger.debug(f"Error downloading {img_url}: {e}")
                continue
        return False

    def _write_image_file(self, path, content):
        with open(path, "wb") as f:
            f.write(content)

    def load_images(self):
        try:
            return os.listdir(self.POKEMON_IMAGES_FOLDER)
        except:
            return []

    async def fetch_all_pokemon_ids(self):
        self.logger.info("Fetching all Pokemon IDs from PokeAPI...")
        pokemon_ids = []
        invalid_ids = {10265, 10266, 10267, 10268, 10269}
        connector = aiohttp.TCPConnector(limit=50)
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            url = "https://pokeapi.co/api/v2/pokemon"
            all_pokemon = []
            page_count = 0
            while url:
                page_count += 1
                self.logger.info(f"Fetching Pokemon list page {page_count}...")
                async with session.get(url) as response:
                    if response.status != 200:
                        break
                    data = await response.json()
                    all_pokemon.extend(data["results"])
                    url = data.get("next")
            self.logger.info(f"Found {len(all_pokemon)} Pokemon entries across {page_count} pages")
            semaphore = asyncio.Semaphore(30)
            tasks = [self._fetch_pokemon_data(semaphore, session, result, invalid_ids) for result in all_pokemon]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            pokemon_ids = [r for r in results if isinstance(r, int)]
        self.logger.info(f"Valid Pokemon IDs collected: {len(pokemon_ids)}")
        return sorted(pokemon_ids)

    async def _fetch_pokemon_data(self, semaphore, session, result, invalid_ids):
        async with semaphore:
            try:
                async with session.get(result["url"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        poke_id = data["id"]
                        if poke_id not in invalid_ids:
                            return poke_id
            except Exception as e:
                self.logger.debug(f"Error fetching Pokemon data for {result.get('name', 'unknown')}: {e}")
        return None

    async def list_existing_emojis(self, server):
        if not server or not server.me.guild_permissions.manage_emojis:
            return {}
        try:
            return {emoji.name: emoji.id for emoji in server.emojis}
        except:
            return {}

    async def upload_single_emoji(self, server, pokemon_id):
        existing_emojis = await self.list_existing_emojis(server)
        emoji_name = str(pokemon_id).zfill(3)
        if emoji_name in existing_emojis:
            return False
        if (str(server.id) in self.emoji_mapping and str(pokemon_id) in self.emoji_mapping[str(server.id)]):
            return False
        if pokemon_id in self.failed_downloads:
            return False
        emoji_image_path = os.path.join(self.POKEMON_IMAGES_FOLDER, f"{emoji_name}.png")
        try:
            emoji_data = await asyncio.get_event_loop().run_in_executor(None, self._read_image_file, emoji_image_path)
            if not emoji_data:
                self.logger.error(f"Could not read image file for Pokemon {pokemon_id}")
                return False
            is_valid, message = self.validate_image_size(emoji_data, server)
            if not is_valid:
                self.logger.error(f"Image validation failed for Pokemon {pokemon_id} on {server.name}: {message}")
                original_data = emoji_data
                resized_data = await asyncio.get_event_loop().run_in_executor(None, self.resize_image_for_discord, original_data, server)
                if resized_data:
                    is_valid, message = self.validate_image_size(resized_data, server)
                    if is_valid:
                        emoji_data = resized_data
                        await asyncio.get_event_loop().run_in_executor(None, self._write_image_file, emoji_image_path, resized_data)
                    else:
                        self.logger.error(f"Could not resize image small enough for Pokemon {pokemon_id}: {message}")
                        return False
                else:
                    return False
            emoji = await server.create_custom_emoji(name=emoji_name, image=emoji_data)
            if str(server.id) not in self.emoji_mapping:
                self.emoji_mapping[str(server.id)] = {}
            self.emoji_mapping[str(server.id)][str(pokemon_id)] = {"name": emoji_name, "id": emoji.id}
            await asyncio.get_event_loop().run_in_executor(None, self._save_emoji_mapping)
            self.logger.info(f"SUCCESS: Uploaded Pokemon {pokemon_id} to {server.name}")
            return True
        except discord.errors.HTTPException as e:
            if e.status == 429:
                retry_after = int(e.response.headers.get("Retry-After", 30))
                self.logger.warning(f"Rate limited, waiting {retry_after}s for Pokemon {pokemon_id}")
                await asyncio.sleep(retry_after)
                return await self.upload_single_emoji(server, pokemon_id)
            elif e.code == 30008:
                self.logger.warning(f"Server {server.name} at emoji capacity")
                return False
            elif e.code == 50045:
                self.logger.error(f"Asset too large for Pokemon {pokemon_id} on {server.name}: {len(emoji_data) if 'emoji_data' in locals() else 'unknown'} bytes")
                return False
            else:
                self.logger.error(f"HTTP Error uploading Pokemon {pokemon_id} to {server.name}: {e}")
                return False
        except Exception as e:
            self.logger.error(f"Unexpected error uploading Pokemon {pokemon_id} to {server.name}: {e}")
            return False

    def _read_image_file(self, path):
        try:
            with open(path, "rb") as f:
                return f.read()
        except:
            return None

    def _save_emoji_mapping(self):
        with open(self.emoji_json_path, "w", encoding="utf-8") as f:
            json.dump(self.emoji_mapping, f, indent=2)

    async def create_emoji_image(self, pokemon_id):
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            return await self.download_single_image(session, pokemon_id)

    async def upload_emojis_for_server(self, servers, global_existing, embed_message=None, ctx=None, embed=None):
        self.logger.info("Starting emoji upload process...")
        available_servers = await self.find_available_servers(min_slots=5)
        if not available_servers:
            message = "ERROR: All servers at emoji capacity!"
            self.logger.warning(message)
            if embed_message and embed:
                embed.description = message
                await embed_message.edit(embed=embed)
            elif ctx:
                await ctx.send(message)
            return
        images = self.load_images()
        pokemon_ids = [int(self.get_pokemon_id(img)) for img in images if str(int(self.get_pokemon_id(img))) not in global_existing and int(self.get_pokemon_id(img)) not in self.failed_downloads]
        if not pokemon_ids:
            self.logger.info("No new Pokemon to upload")
            return
        self.logger.info(f"Uploading {len(pokemon_ids)} Pokemon emojis across {len(available_servers)} servers")
        emojis_uploaded = 0
        server_index = 0
        upload_semaphore = asyncio.Semaphore(5)
        
        async def upload_with_server_rotation(pokemon_id):
            nonlocal server_index, emojis_uploaded
            async with upload_semaphore:
                for attempt in range(len(available_servers)):
                    if not available_servers:
                        return False
                    server = available_servers[server_index % len(available_servers)]
                    current_count = len(await self.list_existing_emojis(server))
                    max_emojis = 50 + (server.premium_tier * 50)
                    if current_count >= max_emojis:
                        available_servers.remove(server)
                        self.logger.info(f"Server {server.name} removed - at capacity")
                        continue
                    result = await self.upload_single_emoji(server, pokemon_id)
                    if result:
                        emojis_uploaded += 1
                        server_index += 1
                        await asyncio.sleep(0.5)
                        return True
                    server_index += 1
                return False

        batch_size = 10
        total_batches = (len(pokemon_ids) + batch_size - 1) // batch_size
        for i in range(0, len(pokemon_ids), batch_size):
            batch = pokemon_ids[i:i + batch_size]
            batch_num = i // batch_size + 1
            self.logger.info(f"Processing upload batch {batch_num}/{total_batches} ({len(batch)} Pokemon)")
            tasks = [upload_with_server_rotation(pid) for pid in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            if not available_servers:
                self.logger.warning("No more available servers, stopping upload")
                break
            if embed_message and embed:
                embed.description = f"Uploading... {emojis_uploaded} emojis added (Batch {batch_num}/{total_batches})"
                await embed_message.edit(embed=embed)
            await asyncio.sleep(2)
        
        final_message = f"SUCCESS: Upload complete! Added {emojis_uploaded}/{len(pokemon_ids)} emojis"
        self.logger.info(final_message)
        if embed_message and embed:
            embed.description = final_message
            embed.color = discord.Color.green()
            await embed_message.edit(embed=embed)

    @commands.command(hidden=True)
    async def create_emojis(self, ctx):
        if ctx.author.id not in self.owner_id:
            await ctx.reply("ERROR: No permission")
            return
        self.logger.info(f"Emoji creation command started by {ctx.author}")
        embed = discord.Embed(description="Starting emoji creation process...", color=discord.Color.blue())
        initial_message = await ctx.send(embed=embed)
        self.emoji_mapping = self.load_emoji_mapping()
        global_existing = set()
        for server_data in self.emoji_mapping.values():
            global_existing.update(server_data.keys())
        self.logger.info(f"Found {len(global_existing)} existing emojis")
        servers = [self.bot.get_guild(int(gid)) for gid in self.GUILD_IDS]
        servers = [s for s in servers if s]
        server_counts = await self.get_server_emoji_counts()
        available_servers = [info['guild'] for info in server_counts.values() if info['available'] > 0]
        if not available_servers:
            embed.description = "ERROR: All servers at capacity!"
            embed.color = discord.Color.red()
            await initial_message.edit(embed=embed)
            return
        embed.description = "Downloading Pokemon images..."
        embed.color = discord.Color.orange()
        await initial_message.edit(embed=embed)
        await self.download_pokemon_images()
        embed.description = "Uploading emojis to servers..."
        embed.color = discord.Color.yellow()
        await initial_message.edit(embed=embed)
        await self.upload_emojis_for_server(servers, global_existing, embed_message=initial_message, ctx=ctx, embed=embed)

    @commands.command(hidden=True)
    async def server_status(self, ctx):
        if ctx.author.id not in self.owner_id:
            await ctx.reply("ERROR: No permission")
            return
        self.logger.info(f"Server status requested by {ctx.author}")
        server_counts = await self.get_server_emoji_counts()
        embed = discord.Embed(title="Server Emoji Status", color=discord.Color.blue())
        total_emojis = sum(info['current'] for info in server_counts.values())
        total_capacity = sum(info['max'] for info in server_counts.values())
        embed.description = f"**Total: {total_emojis}/{total_capacity} emojis used**"
        for guild_id, info in server_counts.items():
            guild = info['guild']
            percentage = (info['current'] / info['max']) * 100
            status_emoji = "RED" if percentage >= 90 else "YELLOW" if percentage >= 70 else "GREEN"
            status = f"{status_emoji} {info['current']}/{info['max']} ({info['available']} free)"
            embed.add_field(name=guild.name[:20], value=status, inline=True)
        await ctx.send(embed=embed)

    def get_emoji_for_pokemon(self, pokemon_id):
        pokemon_id_str = str(pokemon_id).zfill(3)
        for server_id, server_data in self.emoji_mapping.items():
            if str(pokemon_id) in server_data:
                emoji_data = server_data[str(pokemon_id)]
                return f"<:{emoji_data['name']}:{emoji_data['id']}>"
        return None

    def call_emoji(self, emoji_mapping, pokemon_id):
        pokemon_id = pokemon_id['id']
        for server_id, server_data in emoji_mapping.items():
            if str(pokemon_id) in server_data:
                emoji_data = server_data[str(pokemon_id)]
                return f"<:{emoji_data['name']}:{int(emoji_data['id'])}>"
        return None

    @commands.command(hidden=True)
    async def get_pokemon_emoji(self, ctx, pokemon_id: int):
        emoji_str = self.get_emoji_for_pokemon(pokemon_id)
        if emoji_str:
            await ctx.send(f"Pokemon emoji: {emoji_str}")
        else:
            await ctx.send(f"ERROR: No emoji found for Pokemon ID {pokemon_id}")

    @commands.command(hidden=True)
    async def force_download(self, ctx, start_id: int = 1, end_id: int = 2000):
        if ctx.author.id not in self.owner_id:
            return
        self.logger.info(f"Force download requested by {ctx.author} for IDs {start_id}-{end_id}")
        embed = discord.Embed(description=f"Force downloading Pokemon {start_id}-{end_id}...", color=discord.Color.orange())
        msg = await ctx.send(embed=embed)
        pokemon_ids = list(range(start_id, end_id + 1))
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            semaphore = asyncio.Semaphore(60)
            tasks = [self._download_with_semaphore(semaphore, session, pid) for pid in pokemon_ids]
            results = []
            batch_size = 50
            total_batches = (len(tasks) + batch_size - 1) // batch_size
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                batch_num = i // batch_size + 1
                embed.description = f"Downloading batch {batch_num}/{total_batches}..."
                await msg.edit(embed=embed)
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                results.extend(batch_results)
        successful = sum(1 for r in results if r)
        embed.description = f"SUCCESS: Downloaded {successful}/{len(pokemon_ids)} images"
        embed.color = discord.Color.green()
        await msg.edit(embed=embed)
        self.logger.info(f"Force download complete: {successful}/{len(pokemon_ids)} successful")

            
            
            
            
            
            
            
            
class Pokemon_Subcogs:
    
 @staticmethod
 def pokemon_name_to_id(pokemon_name, file_path="data/commands/pokemon/pokemon_names.csv"):
    try:
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row["name"].lower() == pokemon_name.lower():
                    return row["id"]
    except Exception as e:
        print(f"Error: {e}")
        return None
    


class PokemonNameHelper:
    def __init__(self, csv_file=None):
        self.csv_file = csv_file
        self.rare, self.regional = [], []

    


    def load_data(self):
        try:
            with open(self.csv_file, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if row[0]: self.rare.append(row[0].lower().strip())
                    if row[1]: self.regional.append(row[1].lower().strip())
        except FileNotFoundError:
            self.rare, self.regional = [], []

    @staticmethod
    def pokemon_name_to_id(pokemon_name, file_path="data/commands/pokemon/pokemon_names.csv"):
     try:
        with open(file_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row["name"].lower() == pokemon_name.lower():
                    return row["id"]
     except Exception as e:
        print(f"Error: {e}")
        return None
 

    def transform_name(self, name):
        map_ = {"alolan":"-alola","galarian":"-galar","hisuian":"-hisui","paldean":"-paldea","mega":"-mega"}
        name_clean = re.sub(r'[^a-zA-Z\s]', '', name)
        lower = name_clean.lower()
        for k,v in map_.items():
            if k in lower:
                parts = name_clean.split()
                base = parts[1].capitalize() if len(parts)>1 else parts[0].capitalize()
                return f"{base.lower()}{v}", k
        return name_clean, None
    
    def reverse_transform_name(self, name):
     rev_map = {"-alola": "Alolan", "-galar": "Galarian", "-hisui": "Hisuian", "-paldea": "Paldean", "-mega": "Mega"}
     n = name.lower()
     for suf, pre in rev_map.items():
        if n.endswith(suf):
            base = name[:-len(suf)]
            return f"{pre} {base}", pre
     return name, ''
    
    def check_match(self, name):
        rare_match = next((p for p in self.rare if fuzz.ratio(name, p) > 90), None)
        regional_match = next((p for p in self.regional if fuzz.ratio(name, p) > 90), None)
        return rare_match, regional_match


class PokemonNameHelperCollection:
    def transform_name(self, name):
        name = name.lower().strip()
        if any(name.endswith(suffix) for suffix in CollectionViewUI.REGIONAL_SUFFIXES):
            return name, name
        return name, name




























class CollectionViewUI(View):
    REGIONAL_SUFFIXES = ("-alola", "-galar", "-hisui", "-paldea")
    REGIONAL_PREFIXES = {
        "alolan": "-alola",
        "galarian": "-galar",
        "hisuian": "-hisui",
        "paldean": "-paldea"
    }
    REGION_EMOJIS = {
        "paldea": "<:Paldea:1212335178714980403>",
        "sinnoh": "<:Sinnoh:1212335180459544607>",
        "alola": "<:Alola:1212335185228472411>",
        "kalos": "<:Kalos:1212335190656024608>",
        "galar": "<:Galar:1212335192740470876>",
        "pasio": "<:848495108667867139:1212335194628034560>",
        "hoenn": "<:Hoenn:1212335197304004678>",
        "unova": "<:Unova:1212335199095095306>",
        "kanto": "<:Kanto:1212335202341363713>",
        "johto": "<:Kanto:1212335202341363713>"
    }
    FILTER_KEYS = ["rare", "regional", "show_all"]
    FILTER_LABELS = {"rare": "Rare", "regional": "Regional", "show_all": "Showing All"}
    NAV_BUTTONS = [("⏮", 0), ("◀", 1), ("▶", 2), ("⏭", 3)]
    ALL_REGIONS = set(REGION_EMOJIS.keys())

    def __init__(self, ctx, entries, title):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.entries = entries
        self.title = title
        self.page = 0
        self.filters = {k: False for k in self.FILTER_KEYS}
        self.selected_regions = set()
        self.ph = PokemonNameHelperCollection()
        self.description_path = "data/commands/pokemon/pokemon_description.csv"
        self.special_path = "data/commands/pokemon/pokemon_special_names.csv"
        self.name_to_region = self._load_region_map()
        self.rare_names, self.regional_names = self._load_special_names()
        
        self.user_regions = self._extract_user_regions()
        self.has_rare = any(self._is_rare_pokemon(e) for e in self.entries)
        self.has_regional = any(self._is_regional_pokemon(e) for e in self.entries)
        self._update_filtered_entries()
        self._update_embeds()
        self._build_components()

    def _extract_pokemon_name(self, entry):
        return re.sub(r'<:[^:]+:\d+>\s*', '', entry).strip()

    def _normalize_name_to_slug(self, name):
        clean = name.lower().strip()
        for prefix, suffix in self.REGIONAL_PREFIXES.items():
            if clean.startswith(f"{prefix} "):
                base_name = clean[len(prefix) + 1:]
                return base_name + suffix
        return clean

    def _normalize_name(self, name):
        n = self._extract_pokemon_name(name) if '<:' in name else name.lower().strip()
        return self._normalize_name_to_slug(n)

    def convert_regional_name(self, name: str) -> str:
        region_map = {
            "alolan": "-alola",
            "galarian": "-galar",
            "hisuian": "-hisui",
            "paldean": "-paldea"
        }
        name_lower = name.lower().strip()
        for prefix, suffix in region_map.items():
            if name_lower.startswith(f"{prefix} "):
                base_name = name_lower[len(prefix) + 1:]
                return base_name + suffix
        return name_lower

    def _load_region_map(self):
        region_map = {}
        try:
            with open(self.description_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    slug = row["slug"].lower()
                    region = row.get("region", "").strip().lower()
                    if region in self.ALL_REGIONS:
                        region_map[slug] = region
        except Exception:
            pass
        return region_map

    def _load_special_names(self):
        rare, regional = set(), set()
        try:
            with open(self.special_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fields = {k.lower().replace(" ", "").replace("é", "e"): k for k in reader.fieldnames}
                rare_col = fields.get("rarepokemon", "")
                regional_col = fields.get("regionalpokemon", "")
                for row in reader:
                    rare_name = row.get(rare_col, "").strip().lower()
                    regional_name = row.get(regional_col, "").strip().lower()
                    if rare_name:
                        rare.add(rare_name)
                    if regional_name:
                        
                        regional.add(regional_name)
        except Exception as e:
            print(f"Error loading special names: {e}")
            pass
        return rare, regional

    def _extract_user_regions(self):
        regions = set()
        for e in self.entries:
            name = self._extract_pokemon_name(e)
            slug = self._normalize_name_to_slug(name)
            try:
                slug, _ = self.ph.transform_name(slug)
            except:
                pass
            if not any(slug.endswith(sfx) for sfx in self.REGIONAL_SUFFIXES):
                region = self.name_to_region.get(slug)
                if region:
                    regions.add(region)
        return sorted(regions)

    def _is_rare_pokemon(self, entry):
        name = self._extract_pokemon_name(entry)
        slug = self._normalize_name_to_slug(name)
        try:
            slug, _ = self.ph.transform_name(slug)
            return slug in self.rare_names
        except:
            return slug in self.rare_names

    def _is_regional_pokemon(self, entry):
        name = self._extract_pokemon_name(entry)
        raw_name = self.convert_regional_name(name)
        try:
            raw_name, _ = self.ph.transform_name(raw_name)
        except:
            pass
        return raw_name in self.regional_names

    def filter_rare_and_regional(self, type: str, entries: list[str]) -> list[str]:
        ready = []
        for e in entries:
            name = self._extract_pokemon_name(e)
            slug = self._normalize_name_to_slug(name)
            try:
                slug, _ = self.ph.transform_name(slug)
            except:
                pass
            region = self.name_to_region.get(slug) if not any(slug.endswith(s) for s in self.REGIONAL_SUFFIXES) else None

            if type == "rare":
                if slug in self.rare_names:
                    ready.append(e)
            elif type == "regional":
                raw_name = self.convert_regional_name(name)
                try:
                    raw_name, _ = self.ph.transform_name(raw_name)
                except:
                    pass
                print(f"[DEBUG] Regional filter check: Entry='{e}', Name='{name}', Raw='{raw_name}', In regional_names={raw_name in self.regional_names}")
                if raw_name in self.regional_names:
                    ready.append(e)
            elif type == "region_filter":
                if self.selected_regions:
                    if region in self.selected_regions:
                        ready.append(e)
                else:
                    ready.append(e)
            else:
                ready.append(e)

        if type == "regional":
            print(f"[DEBUG] Regional filter result count: {len(ready)} out of {len(entries)} entries")
            print(f"[DEBUG] After regional filter: {len(ready)} entries")

        return ready

    def _update_filtered_entries(self):
        if self.filters["show_all"]:
            self.filtered_entries = self.entries[:]
            return
        entries = self.entries[:]
        if self.filters["rare"]:
            print("[DEBUG] Filter 'rare' toggled to True")
            entries = self.filter_rare_and_regional("rare", entries)
        if self.filters["regional"]:
            print("[DEBUG] Filter 'regional' toggled to True")
            entries = self.filter_rare_and_regional("regional", entries)
        if self.selected_regions:
            entries = self.filter_rare_and_regional("region_filter", entries)
        self.filtered_entries = entries

    def _update_embeds(self):
        chunks = [self.filtered_entries[i:i+CHUNK_SIZE] for i in range(0, len(self.filtered_entries), CHUNK_SIZE)] or [[]]
        self.embeds = []
        for i, chunk in enumerate(chunks):
            start = i * CHUNK_SIZE + 1
            end = start + len(chunk) - 1
            active = [self.FILTER_LABELS[k] for k in self.FILTER_KEYS if k != "show_all" and self.filters[k]]
            if self.selected_regions:
                active.append(f"Regions: {', '.join(sorted(self.selected_regions))}")
            if self.filters["show_all"]:
                active.append(self.FILTER_LABELS["show_all"])
            footer = f"Page {i+1}/{len(chunks)} | Showing entries {start}–{end} out of {len(self.filtered_entries)} | {' | '.join(active) or 'No filters active'}"
            embed = Embed(
                title=self.title,
                description="\n".join(chunk) or "No Pokémon found.",
                color=self.primary_color() if chunk else 0xFF0000
            )
            embed.set_footer(text=footer)
            self.embeds.append(embed)
        self.page = min(self.page, len(self.embeds) - 1)

    def _build_components(self):
        self.clear_items()
        last = len(self.embeds) - 1
        for label, idx in self.NAV_BUTTONS:
            disabled = (idx in (0, 1) and self.page == 0) or (idx in (2, 3) and self.page == last)
            b = Button(label=label, style=ButtonStyle.gray, disabled=disabled, row=0)
            b.callback = [self._first, self._prev, self._next, self._last][idx]
            self.add_item(b)
        region_button_labels = set()
        for e in self.entries:
            name = self._extract_pokemon_name(e).lower()
            for region in self.ALL_REGIONS:
                if name.startswith(region + " "):
                    region_button_labels.add(region)
        for region in sorted(region_button_labels):
            b = Button(
                label=region.capitalize(),
                style=ButtonStyle.primary if region in self.selected_regions else ButtonStyle.secondary,
                row=1
            )
            b.callback = self._region_button_callback(region)
            self.add_item(b)
        region_opts = [r for r in self.user_regions if r not in region_button_labels]
        opts = [
            SelectOption(
                label=r.capitalize(),
                value=r,
                emoji=self.REGION_EMOJIS.get(r),
                default=r in self.selected_regions
            )
            for r in region_opts
        ]
        if opts:
            class RegionSelect(Select):
                def __init__(s):
                    super().__init__(placeholder="Select Regions...", options=opts, min_values=0, max_values=len(opts), row=2)
                async def callback(s, interaction):
                    await self._region_select(interaction, s.values)
            self.add_item(RegionSelect())
        if self.has_rare:
            b = Button(
                label=self.FILTER_LABELS["rare"],
                style=ButtonStyle.success if self.filters["rare"] else ButtonStyle.secondary,
                row=3
            )
            b.callback = self._toggle("rare")
            self.add_item(b)
        if self.has_regional:
            b = Button(
                label=self.FILTER_LABELS["regional"],
                style=ButtonStyle.success if self.filters["regional"] else ButtonStyle.secondary,
                row=3
            )
            b.callback = self._toggle("regional")
            self.add_item(b)
        if any(self.filters[k] for k in ("rare", "regional")) or self.selected_regions:
            b = Button(
                label=self.FILTER_LABELS["show_all"],
                style=ButtonStyle.primary if self.filters["show_all"] else ButtonStyle.secondary,
                row=3
            )
            b.callback = self._toggle("show_all", clear_others=True)
            self.add_item(b)

    def _region_button_callback(self, region):
        async def cb(interaction):
            if region in self.selected_regions:
                self.selected_regions.remove(region)
            else:
                self.selected_regions.add(region)
            self.filters["show_all"] = False
            self._update_filtered_entries()
            self._update_embeds()
            self._build_components()
            await interaction.response.edit_message(embed=self.embeds[self.page], view=self)
        return cb

    def _toggle(self, key, clear_others=False):
        async def cb(interaction):
            if clear_others:
                self.filters = {k: False for k in self.filters}
                self.selected_regions.clear()
            self.filters[key] = not self.filters[key]
            self._update_filtered_entries()
            self._update_embeds()
            self._build_components()
            await interaction.response.edit_message(embed=self.embeds[self.page], view=self)
        return cb

    async def _region_select(self, interaction, values):
        self.selected_regions = set(values)
        self.filters["show_all"] = False
        self._update_filtered_entries()
        self._update_embeds()
        self._build_components()
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    async def _first(self, interaction):
        self.page = 0
        await self._refresh(interaction)

    async def _prev(self, interaction):
        self.page = max(0, self.page - 1)
        await self._refresh(interaction)

    async def _next(self, interaction):
        self.page = min(self.page + 1, len(self.embeds) - 1)
        await self._refresh(interaction)

    async def _last(self, interaction):
        self.page = len(self.embeds) - 1
        await self._refresh(interaction)

    async def _refresh(self, interaction):
        self._update_embeds()
        self._build_components()
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author


 

















































































