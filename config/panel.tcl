#############################################################################
# Generated by PAGE version 4.5
# in conjunction with Tcl version 8.6
#    Feb 21, 2016 06:00:47 PM


set vTcl(actual_gui_bg) #d9d9d9
set vTcl(actual_gui_fg) #000000
set vTcl(actual_gui_menu_bg) #d9d9d9
set vTcl(actual_gui_menu_fg) #000000
set vTcl(complement_color) #d9d9d9
set vTcl(analog_color_p) #d9d9d9
set vTcl(analog_color_m) #d9d9d9
set vTcl(active_fg) #111111
#################################
#LIBRARY PROCEDURES
#


if {[info exists vTcl(sourcing)]} {

proc vTcl:project:info {} {
    set base .top37
    namespace eval ::widgets::$base {
        set dflt,origin 0
        set runvisible 1
    }
    namespace eval ::widgets_bindings {
        set tagslist _TopLevel
    }
    namespace eval ::vTcl::modules::main {
        set procs {
        }
        set compounds {
        }
        set projectType single
    }
}
}

#################################
# USER DEFINED PROCEDURES
#

#################################
# GENERATED GUI PROCEDURES
#

proc vTclWindow.top37 {base} {
    if {$base == ""} {
        set base .top37
    }
    if {[winfo exists $base]} {
        wm deiconify $base; return
    }
    set top $base
    ###################
    # CREATING WIDGETS
    ###################
    vTcl::widgets::core::toplevel::createCmd $top -class Toplevel \
        -background {#d9d9d9} 
    wm focusmodel $top passive
    wm geometry $top 1123x366+522+115
    update
    # set in toplevel.wgt.
    global vTcl
    set vTcl(save,dflt,origin) 0
    wm maxsize $top 4476 1483
    wm minsize $top 120 1
    wm overrideredirect $top 0
    wm resizable $top 1 1
    wm deiconify $top
    wm title $top "SH Mobot Preview"
    vTcl:DefineAlias "$top" "Toplevel1" vTcl:Toplevel:WidgetProc "" 1
    label $top.lab38 \
        -background {#d4d4d4} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {No Signal} 
    vTcl:DefineAlias "$top.lab38" "V1" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab39 \
        -background {#d4d4d4} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {No Signal} 
    vTcl:DefineAlias "$top.lab39" "V2" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab40 \
        -background {#d4d4d4} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {No Signal} 
    vTcl:DefineAlias "$top.lab40" "V3" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab41 \
        -background {#d4d4d4} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {No Signal} 
    vTcl:DefineAlias "$top.lab41" "V4" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab42 \
        -background {#d4d4d4} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {No Signal} 
    vTcl:DefineAlias "$top.lab42" "V5" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab43 \
        -background {#d4d4d4} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {No Signal} 
    vTcl:DefineAlias "$top.lab43" "V6" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab44 \
        -background {#d4d4d4} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {No Signal} 
    vTcl:DefineAlias "$top.lab44" "V7" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab45 \
        -background {#d4d4d4} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {No Signal} 
    vTcl:DefineAlias "$top.lab45" "V8" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab46 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text {Original Video} 
    vTcl:DefineAlias "$top.lab46" "VL1" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab47 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text Processed 
    vTcl:DefineAlias "$top.lab47" "VL2" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab48 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text Processed 
    vTcl:DefineAlias "$top.lab48" "VL3" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab49 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text Processed 
    vTcl:DefineAlias "$top.lab49" "VL4" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab50 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text Processed 
    vTcl:DefineAlias "$top.lab50" "VL5" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab51 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text Processed 
    vTcl:DefineAlias "$top.lab51" "VL6" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab52 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text Processed 
    vTcl:DefineAlias "$top.lab52" "VL7" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab53 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text Processed 
    vTcl:DefineAlias "$top.lab53" "VL8" vTcl:WidgetProc "Toplevel1" 1
    ttk::scale $top.tSc54 \
        -to 100 -takefocus {} 
    vTcl:DefineAlias "$top.tSc54" "S1" vTcl:WidgetProc "Toplevel1" 1
    bind $top.tSc54 <ButtonRelease-1> {
        lambda e: updateValue(e)
    }
    ttk::scale $top.tSc55 \
        -to 100 -takefocus {} 
    vTcl:DefineAlias "$top.tSc55" "S2" vTcl:WidgetProc "Toplevel1" 1
    bind $top.tSc55 <ButtonRelease-1> {
        lambda e: updateValue(e)
    }
    ttk::scale $top.tSc56 \
        -to 100 -takefocus {} 
    vTcl:DefineAlias "$top.tSc56" "S3" vTcl:WidgetProc "Toplevel1" 1
    bind $top.tSc56 <ButtonRelease-1> {
        lambda e: updateValue(e)
    }
    ttk::scale $top.tSc57 \
        -to 100 -takefocus {} 
    vTcl:DefineAlias "$top.tSc57" "S4" vTcl:WidgetProc "Toplevel1" 1
    bind $top.tSc57 <ButtonRelease-1> {
        lambda e: updateValue(e)
    }
    ttk::scale $top.tSc58 \
        -to 100 -takefocus {} 
    vTcl:DefineAlias "$top.tSc58" "S5" vTcl:WidgetProc "Toplevel1" 1
    bind $top.tSc58 <ButtonRelease-1> {
        lambda e: updateValue(e)
    }
    ttk::scale $top.tSc59 \
        -to 100 -takefocus {} 
    vTcl:DefineAlias "$top.tSc59" "S6" vTcl:WidgetProc "Toplevel1" 1
    bind $top.tSc59 <ButtonRelease-1> {
        lambda e: updateValue(e)
    }
    label $top.lab60 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text S1 
    vTcl:DefineAlias "$top.lab60" "SL1" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab61 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text S2 
    vTcl:DefineAlias "$top.lab61" "SL2" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab62 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text S3 
    vTcl:DefineAlias "$top.lab62" "SL3" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab63 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text S4 
    vTcl:DefineAlias "$top.lab63" "SL4" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab64 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text S5 
    vTcl:DefineAlias "$top.lab64" "SL5" vTcl:WidgetProc "Toplevel1" 1
    label $top.lab65 \
        -background {#d9d9d9} -disabledforeground {#a3a3a3} \
        -foreground {#000000} -text S6 
    vTcl:DefineAlias "$top.lab65" "SL6" vTcl:WidgetProc "Toplevel1" 1
    ###################
    # SETTING GEOMETRY
    ###################
    place $top.lab38 \
        -in $top -x 30 -y 30 -width 160 -height 120 -anchor nw \
        -bordermode ignore 
    place $top.lab39 \
        -in $top -x 210 -y 30 -width 160 -height 120 -anchor nw \
        -bordermode ignore 
    place $top.lab40 \
        -in $top -x 390 -y 30 -width 160 -height 120 -anchor nw \
        -bordermode ignore 
    place $top.lab41 \
        -in $top -x 570 -y 30 -width 160 -height 120 -anchor nw \
        -bordermode ignore 
    place $top.lab42 \
        -in $top -x 30 -y 190 -width 160 -height 120 -anchor nw \
        -bordermode ignore 
    place $top.lab43 \
        -in $top -x 210 -y 190 -width 160 -height 120 -anchor nw \
        -bordermode ignore 
    place $top.lab44 \
        -in $top -x 390 -y 190 -width 160 -height 120 -anchor nw \
        -bordermode ignore 
    place $top.lab45 \
        -in $top -x 570 -y 190 -width 160 -height 120 -anchor nw \
        -bordermode ignore 
    place $top.lab46 \
        -in $top -x 70 -y 160 -anchor nw -bordermode ignore 
    place $top.lab47 \
        -in $top -x 260 -y 160 -anchor nw -bordermode ignore 
    place $top.lab48 \
        -in $top -x 440 -y 160 -anchor nw -bordermode ignore 
    place $top.lab49 \
        -in $top -x 620 -y 160 -anchor nw -bordermode ignore 
    place $top.lab50 \
        -in $top -x 80 -y 320 -anchor nw -bordermode ignore 
    place $top.lab51 \
        -in $top -x 260 -y 320 -anchor nw -bordermode ignore 
    place $top.lab52 \
        -in $top -x 440 -y 320 -anchor nw -bordermode ignore 
    place $top.lab53 \
        -in $top -x 620 -y 320 -anchor nw -bordermode ignore 
    place $top.tSc54 \
        -in $top -x 800 -y 30 -anchor nw -bordermode ignore 
    place $top.tSc55 \
        -in $top -x 800 -y 80 -anchor nw -bordermode ignore 
    place $top.tSc56 \
        -in $top -x 800 -y 130 -anchor nw -bordermode ignore 
    place $top.tSc57 \
        -in $top -x 800 -y 180 -anchor nw -bordermode ignore 
    place $top.tSc58 \
        -in $top -x 800 -y 230 -anchor nw -bordermode ignore 
    place $top.tSc59 \
        -in $top -x 800 -y 280 -anchor nw -bordermode ignore 
    place $top.lab60 \
        -in $top -x 750 -y 30 -anchor nw -bordermode ignore 
    place $top.lab61 \
        -in $top -x 750 -y 80 -anchor nw -bordermode ignore 
    place $top.lab62 \
        -in $top -x 750 -y 130 -anchor nw -bordermode ignore 
    place $top.lab63 \
        -in $top -x 750 -y 180 -anchor nw -bordermode ignore 
    place $top.lab64 \
        -in $top -x 750 -y 230 -anchor nw -bordermode ignore 
    place $top.lab65 \
        -in $top -x 750 -y 280 -anchor nw -bordermode ignore 

    vTcl:FireEvent $base <<Ready>>
}

#############################################################################
## Binding tag:  _TopLevel

bind "_TopLevel" <<Create>> {
    if {![info exists _topcount]} {set _topcount 0}; incr _topcount
}
bind "_TopLevel" <<DeleteWindow>> {
    if {[set ::%W::_modal]} {
                vTcl:Toplevel:WidgetProc %W endmodal
            } else {
                destroy %W; if {$_topcount == 0} {exit}
            }
}
bind "_TopLevel" <Destroy> {
    if {[winfo toplevel %W] == "%W"} {incr _topcount -1}
}

Window show .
Window show .top37
