###############################
########## VARIABLES ##########
###############################

WHITE = "#FCFCFC"
# WHITE = "#FFFFFF"

#### TEXT ####
WDGT_FONT = "13pt DM Sans"
LABELS_COLOR = WHITE

#### BACKGROUND ####
# BACKGROUND_COLOR = "#2F4858"
BACKGROUND_COLOR = "rgb(28, 30, 42)"

#### BUTTONS ####
BTN_TEXT_COLOR = WHITE
BTN_COLOR = "rgb(84, 89, 124)"
BTN_BORDER = "2px solid rgb(84, 89, 124)"
BTN_BORDER_RADIUS = "5px"
BTN_PADDING = "5px"

#HOVER
BTN_HOVER_COLOR = "rgb(61, 64, 89)"

#PRESSED
BTN_PRESSED_COLOR = "rgb(61, 64, 89)"
BTN_PRESSED_BORDER = "2px solid rgb(61, 64, 89)"

#### CHECKBOX ####
CB_TEXT_COLOR = WHITE

#### TOOLTIP ####
TTIP_BG_COLOR = "transparent"
TTIP_TEXT_COLOR = WHITE
TTIP_BORDER = "1px solid rgb(218, 217, 219)"

#### TOOLTIP ####
DD_TEXT_COLOR = WHITE
DD_TEXT_BORDER = f"1px solid {WHITE}"


#### TOP BAR (HEADER) ####
HEADER_BG_COLOR = "rgb(27, 29, 39)"
HEADER_BORDER = "2px solid rgb(95, 197, 201)"
HEADER_BTN_PRESSED_COLOR = "rgb(101, 106, 141)"


#### FOOTER ####
FOOTER_BG_COLOR = "rgb(27, 29, 39)"
FOOTER_BORDER = "1px solid rgb(95, 197, 201)"

#### LEFT MENU ####
LM_BORDER = "1px solid rgb(95, 197, 201)"

#BUTTONS
LM_BTN_TXT_COLOR = "rgb(189, 189, 189)"
LM_BTN_HOVER_COLOR = "rgb(61, 64, 89)"
LM_BTN_PRESSED_COLOR = "rgb(113, 120, 159)"



#### TITLES ####
TITLES = {
	"TEXT_COLOR" : WHITE,
	"FONT" : "26pt DM Sans",
	"BORDER" : f"1px solid {WHITE}"
}

#### TABS VISUALIZATION ####
TAB_PANE_BORDER = f"1px solid {WHITE}"
TAB_BAR_BG_COLOR = "transparent"
TAB_BAR_TEXT_COLOR = WHITE
TAB_BAR_BORDER = "1px solid rgb(228, 227, 229)"

TAB_ON_BG_COLOR = "rgba(49, 52, 86, 215)"
TAB_ON_TEXT_COLOR = WHITE
TAB_ON_TEXT_BORDER = "2px solid rgb(255, 255, 255)"

TAB_HOVER_TEXT = "underline"

#### TABS VISUALIZATION ####

################################
########## GENERATORS ##########
################################
BTN_STYLESHEET = f"""
QPushButton{{
	color: {BTN_TEXT_COLOR};
	background-color: {BTN_COLOR};
	border: {BTN_BORDER};
	padding: {BTN_PADDING};
	border-radius: {BTN_BORDER_RADIUS};
	font: 12pt;

}}

QPushButton:hover{{
	background-color: {BTN_HOVER_COLOR};
}}

QPushButton:pressed{{
	background-color: {BTN_PRESSED_COLOR};
	border:  {BTN_PRESSED_BORDER};
}}
"""

HEADER_BTN_STYLESHEET = f"""
QPushButton{{
	color: {BTN_TEXT_COLOR};
	background-color: {BTN_COLOR};
	border: {BTN_BORDER};
	padding: {BTN_PADDING};
	border-radius: {BTN_BORDER_RADIUS};

}}

QPushButton:hover{{
	background-color: {BTN_HOVER_COLOR};
}}

QPushButton:pressed{{
	background-color: {HEADER_BTN_PRESSED_COLOR};
	border:  {BTN_PRESSED_BORDER};
}}
""" 

def stylesheet_titles(title):
	txt_color = title["TEXT_COLOR"]
	font = title["FONT"]
	border = title["BORDER"]

	titles = ["integration_title", "home_title", "impedance_title", "settings_title"]
	frames = ["frame_integration_title", "frame_home_title", "frame_impedance_title", "frame_settings_title"]

	stylesheet = ""

	for title, frame in zip(titles, frames):
		title_stylesheet = f"""
		QLabel#{title}{{
		color: {txt_color};
		border:none;
		font: {font};
		}}

		QFrame#{frame}{{
		border-bottom: {border};
		border-top: none;
		border-left: none;
		border-right: none;
		}}
		"""

		stylesheet += title_stylesheet

	return stylesheet


TITLES_STYLESHEET = stylesheet_titles(TITLES)

###############################
##### CENTRAL STYLE SHEET #####
###############################

CENTRAL_STYLESHEET = f"""
/*GENERAL*/
QWidget{{
	font: {WDGT_FONT};
}}
 
QFrame{{
	background-color: {BACKGROUND_COLOR};
	border: none;
}}

QLabel{{
	color: {LABELS_COLOR};
	/*font: 13pt ""*/
}}

{HEADER_BTN_STYLESHEET}

QCheckBox{{
	color: {CB_TEXT_COLOR};
}}

QToolTip{{
	background-color: {TTIP_BG_COLOR};
	color: {TTIP_TEXT_COLOR};
	border: {TTIP_BORDER};
}}

QComboBox{{
	color: {DD_TEXT_COLOR};
	border: {DD_TEXT_BORDER}
}}

#centralwidget{{
	background-color: {BACKGROUND_COLOR};
}}

/*HEADER*/
#main_header{{
	background-color: {HEADER_BG_COLOR};
	border-bottom: {HEADER_BORDER};
}}

#main_header .QFrame{{
	border: none;
}}

#top_right_btns .QPushButton{{
	background-color: {HEADER_BG_COLOR};
	border-radius: 5px;
	border: none
}}

#top_right_btns .QPushButton:hover{{
	background-color: {BTN_HOVER_COLOR};
}}


/*FOOTER*/
#main_footer{{
	background-color: {FOOTER_BG_COLOR};
	border-top: {FOOTER_BORDER}; 
}}

/*LEFT SIDE MENU*/
#left_side_menu {{
	border:none;
	border-right: {LM_BORDER};
}}

#toggle_left_menu{{
	border:none;
}}

#btns_left_menu{{
	border:none;
}}

#left_side_menu .QPushButton{{
	border-radius: 5px;
	background-position: left center;
    	background-repeat: no-repeat;
	border: none;
	border-left: 20px solid transparent;
	text-align: left;
	padding-left: 44px;
	color: {LM_BTN_TXT_COLOR};
}}

#left_side_menu .QPushButton:hover {{
	background-color: {LM_BTN_HOVER_COLOR};
	border-left: 20px solid {LM_BTN_HOVER_COLOR};

}}
#left_side_menu .QPushButton:pressed {{
	background-color: {LM_BTN_PRESSED_COLOR};
	border-left:  20px solid {LM_BTN_PRESSED_COLOR};
}}

/*button icons*/
#btn_home{{
	background-image: url(:/icons/icons/cil-home.png);
}}

#btn_impedance{{
	background-image: url(:/icons/icons/cil-speedometer.png);
}}

#btn_integration{{
	background-image: url(:/icons/icons/cil-share-boxed.png);
}}

#btn_plots{{
	background-image: url(:/icons/icons/cil-chart-line.png);
}}

#btn_settings{{
	background-image: url(:/icons/icons/cil-settings.png);
}}

#btn_left_menu_toggle{{
	background-image: url(:/icons/icons/icon_menu.png);
}}

/*TITLES FONT*/

{TITLES_STYLESHEET}

/*TABS VISUALIZATION*/
QTabWidget::pane{{
	border: {TAB_PANE_BORDER}
}}
QTabWidget::tab-bar{{
	alignment: left;
}}
QTabBar::tab 
{{
    background: {TAB_BAR_BG_COLOR};
    color: {TAB_BAR_TEXT_COLOR};
	border: {TAB_BAR_BORDER};
	/*margin-left: 2;
	margin-right: 2;*/
	width: 100px;
	padding: 2px
}}

QTabBar::tab:selected
{{
	background: {TAB_ON_BG_COLOR};
    color: {TAB_ON_TEXT_COLOR};   
    border: {TAB_ON_TEXT_BORDER};
}}, 
QTabBar::tab:hover 
{{
	text-decoration: {TAB_HOVER_TEXT};
}}
"""

MAINBODY_STYLESHEET = f"""
	background-color: {BACKGROUND_COLOR}
"""