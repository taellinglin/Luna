from color_tokens import thematic_tokens

for i, item in enumerate(thematic_tokens.keys()):
    try:
        del thematic_tokens[item]["Gray10"]
        del thematic_tokens[item]["Gray90"]
    except:
        pass

with open("./color_toke.py", "w", encoding="utf-8") as myf:
    myf.write(f"{thematic_tokens}")
