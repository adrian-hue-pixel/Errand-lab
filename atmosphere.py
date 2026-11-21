"""Workspace theme and responsive component styles. Both palettes use opaque text colors."""
from layout import rule, keyframes


DARK={"bg":"#0b1717","paper":"#172b2b","ink":"#f0f5e9","tone":"#c3d3c9","accent":"#9ee4bd",
      "select":"#29483e","line":"#708880","glass":"rgba(22,44,43,.93)","deep":"#0c211e","control":"#162e29",
      "primary":"#c5e8ac","onprimary":"#142b21","glow":"#327d62","errorbg":"#402b2a","errorink":"#ffdbce"}
LIGHT={"bg":"#eef1e8","paper":"#fffef8","ink":"#152e28","tone":"#435b51","accent":"#1e664b",
       "select":"#dce9d9","line":"#819487","glass":"rgba(251,253,243,.94)","deep":"#ecf2e7","control":"#fbfcf4",
       "primary":"#245740","onprimary":"#ffffff","glow":"#90b79c","errorbg":"#ffede6","errorink":"#732e21"}


def stylesheet():
    dark=rule(":root",**{"--"+k:v for k,v in DARK.items()},color_scheme="dark")
    light=rule(':root[data-theme="light"]',**{"--"+k:v for k,v in LIGHT.items()},color_scheme="light")
    styles={
        "body":dict(color="var(--ink)",background="var(--bg)",min_height="100vh",isolation="isolate"),
        ".atmos":dict(position="fixed",inset="0",overflow="hidden",z_index="-1",pointer_events="none",
                      background_image="linear-gradient(#83998e0e 1px,transparent 1px),linear-gradient(90deg,#83998e0e 1px,transparent 1px)",
                      background_size="48px 48px"),
        ".atmos i":dict(position="absolute",width="72vmax",height="72vmax",border_radius="50%",top="-35vmax",right="-14vmax",
                        background="radial-gradient(ellipse at center,var(--glow),transparent 66%)",opacity=".43"),
        ".atmos i+i":dict(top="48vh",left="-42vmax",opacity=".29"),
        ".workspace":dict(display="grid",grid_template_columns="240px minmax(0,1fr)"),
        ".rail":dict(position="sticky",top="0",height="100dvh",padding="32px 16px",background="var(--glass)",border_right="1px solid var(--line)",
                     display="flex",flex_direction="column",gap="24px",z_index="3",backdrop_filter="blur(16px)"),
        ".rail .brand":dict(color="var(--ink)",gap="8px"),
        ".rail .collapse":dict(align_self="flex-end"),
        ".rail nav":dict(display="grid",gap="6px",background="transparent",width="100%",padding="0"),
        ".rail nav a":dict(color="var(--tone)",justify_content="flex-start",padding="12px",gap="12px"),
        ".rail nav a[aria-current]":dict(background="var(--select)",color="var(--ink)"),
        ".railfoot":dict(margin_top="auto",font="600 10px ui-monospace,monospace",letter_spacing=".1em",color="var(--tone)"),
        ".desk":dict(min_width="0"),
        ".utilities":dict(display="flex",align_items="center",gap="16px",min_height="72px",justify_content="space-between",
                          padding="8px clamp(16px,4vw,64px)",border_bottom="1px solid var(--line)",background="var(--glass)"),
        ".tools,.profilepill,.wordmark":dict(display="flex",align_items="center",gap="12px"),
        ".profilepill":dict(color="var(--ink)",text_decoration="none",font_weight="650",overflow="hidden",max_width="190px",overflow_wrap="anywhere"),
        ".iconbtn,.notify summary,.dialogbtn":dict(display="inline-grid",place_items="center",border="1px solid var(--line)",border_radius="12px",
                                                 background="var(--paper)",color="var(--ink)",width="42px",height="42px",cursor="pointer"),
        ".notify":dict(position="relative"),
        ".notify div":dict(position="absolute",right="0",top="48px",padding="16px",width="220px",background="var(--paper)",border="1px solid var(--line)",border_radius="12px",z_index="4"),
        ".container":dict(width="min(1160px,calc(100% - 64px))",margin="auto",padding_bottom="120px"),
        ".card,.pending,.planner-actions,.case,.prefs,dialog":dict(color="var(--ink)",background="var(--glass)",border="1px solid var(--line)",backdrop_filter="blur(16px)",box_shadow="0 16px 56px -36px #04121088"),
        ".button.quiet,.chip,.chips,.caseicon,.stopnum,.key span,.tag,.stop,.stopeditor,.benchgrid>section,.stopeditor summary:hover,.metric:first-child,.current,thead":dict(background="var(--select)",color="var(--ink)"),
        ".primary,.primary:is(:hover,:focus-visible)":dict(background="var(--primary)",color="var(--onprimary)"),
        ".chip[aria-current],.button[aria-pressed=true]":dict(background="var(--primary)",color="var(--onprimary)"),
        ".quiet:hover,.rail nav a:hover":dict(background="var(--select)",color="var(--ink)"),
        "label,input,textarea,select,summary,b,strong,h1,h2,h3":dict(color="var(--ink)"),
        "input,select,textarea":dict(background="var(--control)",color="var(--ink)",border="1px solid var(--line)"),
        "textarea":dict(width="100%",border_radius="10px",padding="12px",font="inherit"),
        ".notice,.tag":dict(background="var(--select)",color="var(--ink)"),
        ".error":dict(background="var(--errorbg)",color="var(--errorink)"),
        ".caseicon,.eyebrow,em,.metric:first-child strong":dict(color="var(--accent)"),
        ".entry":dict(min_height="100dvh",max_width="1380px",margin="auto",display="grid",grid_template_columns="minmax(0,1.2fr) minmax(340px,.8fr)",
                      align_items="center",gap="clamp(40px,8vw,128px)",padding="clamp(32px,6vw,100px)"),
        ".entry-story":dict(display="grid",gap="clamp(24px,5vh,64px)",align_content="center"),
        ".wordmark":dict(font_size="24px",font_weight="770",letter_spacing="-.06em"),
        ".wordmark svg":dict(background="var(--primary)",color="var(--onprimary)",width="38px",height="38px",padding="8px",border_radius="12px"),
        ".entry h1":dict(font_size="clamp(54px,7.8vw,110px)",line_height=".95",letter_spacing="-.073em"),
        ".entry-copy>p:last-child":dict(max_width="43ch",font_size="18px",margin_top="24px"),
        ".cartograph":dict(position="relative",max_width="520px",color="var(--accent)"),
        ".cartograph>svg:first-child":dict(width="100%",height="auto"),
        ".cartograph .mascot":dict(position="absolute",right="8%",top="-12px"),
        ".auth":dict(padding="clamp(24px,3.5vw,52px)"),
        ".auth form,.prefs form":dict(display="grid",gap="16px",margin="24px 0"),
        ".check":dict(display="flex",align_items="center",gap="10px",margin="12px 0",font_size="14px"),
        ".check input":dict(width="18px",height="18px",min_height="0",margin="0",accent_color="var(--accent)"),
        ".prefs":dict(max_width="760px",margin="24px 0",padding="clamp(20px,3vw,40px)"),
        ".prefs>label":dict(margin_top="16px"),
        ".prefs output":dict(display="block",color="var(--tone)",margin_top="12px"),
        ".featured":dict(display="grid",grid_template_columns="minmax(0,.9fr) minmax(0,1.2fr)",align_items="center",gap="32px",padding="clamp(24px,3vw,48px)"),
        ".featured h2":dict(font_size="clamp(34px,4.5vw,68px)"),
        ".dash-metrics,.telemetry":dict(display="grid",grid_template_columns="repeat(3,minmax(0,1fr))",gap="16px",margin_top="24px"),
        ".dash-metric":dict(display="grid",gap="12px",text_decoration="none",color="var(--ink)"),
        ".dash-metric strong,.telemetry strong":dict(display="block",font_size="clamp(24px,3vw,40px)",letter_spacing="-.045em"),
        ".dash-metric span":dict(font_size="13px",color="var(--tone)"),
        ".dock":dict(position="fixed",right="24px",bottom="24px",display="flex",align_items="center",gap="8px",padding="0 20px 0 8px",
                     color="var(--ink)",background="var(--paper)",border="1px solid var(--line)",border_radius="28px",box_shadow="0 8px 24px #0003",z_index="4",cursor="pointer"),
        "dialog":dict(width="min(440px,calc(100% - 24px))",max_height="85dvh",border_radius="20px",padding="24px",margin="auto 16px 16px auto"),
        "dialog::backdrop":dict(background="#06110da6"),
        "dialog header,dialog header div":dict(display="flex",align_items="center",justify_content="space-between",gap="12px"),
        "dialog button,.starters button":dict(border="1px solid var(--line)",background="var(--control)",color="var(--ink)",border_radius="12px",padding="8px 12px",cursor="pointer"),
        "#messages":dict(max_height="32dvh",overflow="auto"),
        ".bubble":dict(padding="12px",background="var(--select)",border_radius="14px",color="var(--ink)",overflow_wrap="anywhere",white_space="pre-wrap"),
        ".bubble.user":dict(margin_left="24px",background="var(--control)"),
        ".starters":dict(display="flex",gap="8px",flex_wrap="wrap",margin="12px 0"),
        "#chat-form .button":dict(margin="12px 0"),
        ".stage":dict(position="relative",aspect_ratio="16/9",min_height="200px",background="var(--deep)",border_radius="16px",overflow="hidden"),
        ".stage canvas,.stage video":dict(display="block",width="100%",height="100%",position="absolute",inset="0",object_fit="contain"),
        ".stage canvas":dict(touch_action="none"),
        ".waiting":dict(position="absolute",inset="0",display="grid",place_content="center",justify_items="center",text_align="center",padding="16px",z_index="1",pointer_events="none"),
        ".waiting>div":dict(width="min(320px,72%)",margin="0 auto 12px"),
        ".studio-controls":dict(display="flex",align_items="center",flex_wrap="wrap",gap="12px",margin="16px 0"),
        ".studio-controls label":dict(flex="1 1 140px"),
        ".mobilemenu,[hidden]":dict(display="none!important"),
        "button:disabled":dict(opacity=".65",cursor="default"),
        ".workspace .mark":dict(color="var(--onprimary)",background="var(--primary)"),
    }
    narrow={
        ".workspace":dict(display="block"),
        ".rail":dict(position="fixed",left="0",top="64px",height="calc(100dvh - 64px)",width="240px",display="none"),
        ':root[data-menu-open="yes"] .rail':dict(display="flex"),
        ".rail .collapse":dict(display="none"),
        ".mobilemenu":dict(display="inline-grid!important"),
        ".utilities":dict(min_height="64px",gap="8px",padding="8px 12px"),
        ".tools":dict(gap="6px"),
        ".utilities>b":dict(display="none"),
        ".container":dict(width="calc(100% - 24px)"),
        ".entry":dict(display="block",padding="32px 20px"),
        ".entry-story":dict(gap="24px"),
        ".entry-copy>p:last-child":dict(font_size="16px"),
        ".cartograph":dict(display="none"),
        ".auth":dict(margin_top="24px"),
        ".featured,.dash-metrics,.telemetry":dict(grid_template_columns="1fr"),
        ".stage":dict(aspect_ratio="4/3"),
        ".profilepill":dict(max_width="132px",font_size="13px"),
        ".dock":dict(bottom="12px",right="12px"),
        ".waiting>div":dict(max_width="170px"),
    }
    compact={'.workspace':dict(grid_template_columns="80px minmax(0,1fr)"),
             '.rail .brand':dict(font_size="0"),'.rail nav span,.railfoot':dict(display="none"),
             '.rail nav a':dict(justify_content="center"),'.rail .collapse':dict(align_self="center")}
    def emit(recipes): return "".join(rule(k,**v) for k,v in recipes.items())
    motion=keyframes("drift",[("from",dict(transform="translate3d(var(--px,0px),var(--py,0px),0) scale(1)")),
                              ("to",dict(transform="translate3d(7%,5%,0) scale(1.08)"))])
    motion+=rule(':root:not([data-motion="Off"]) .atmos i',animation="drift 20s ease-in-out infinite alternate")
    motion+=rule(':root[data-motion="Subtle"] .atmos i',animation_duration="38s",opacity=".22")
    motion+=rule(".atmos i+i",animation_delay="-9s")
    motion+=keyframes("ear",[("48%,52%",dict(rotate="0deg")),("50%",dict(rotate="-8deg"))])
    motion+=rule(".ear",transform_origin="center",transform_box="fill-box",animation="ear 5s ease infinite")
    motion+=rule('[data-state="thinking"] .float',animation="think .7s ease-in-out infinite alternate")
    motion+=rule('[data-state="speaking"] .float',animation="cheer .8s ease-in-out infinite")
    motion+=rule('[data-state="listening"] .gaze',transform="translate(-2px,-1px)")
    return dark+light+emit(styles)+"@media(min-width:761px){"+emit({':root[data-rail-small="yes"] '+k.replace(',',',:root[data-rail-small="yes"] '):v for k,v in compact.items()})+"}"+'@media(max-width:760px){'+emit(narrow)+'}'+'@media(prefers-reduced-motion:no-preference){'+motion+'}'
