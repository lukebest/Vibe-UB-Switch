# Stub project commands that xsim GUI (File > Open Waveform Database)
# calls. This install has no FPGA parts, so `load_feature core` + real
# `current_fileset` raises Project 1-848. A Tcl stub is enough for WDB view.
namespace eval ::vibe_xsim_gui {}

proc ::vibe_xsim_gui::install_fileset_stub {} {
  set body ""
  catch {set body [info body ::current_fileset]}
  if {[string match *vibe_xsim_gui* $body]} {
    return
  }
  if {[info commands ::_vibe_current_fileset_orig] ne ""} {
    catch {rename ::_vibe_current_fileset_orig {}}
  }
  if {[info commands ::current_fileset] ne ""} {
    catch {rename ::current_fileset ::_vibe_current_fileset_orig}
  }
  proc ::current_fileset {args} {
    # marker: vibe_xsim_gui
    if {[info commands ::_vibe_current_fileset_orig] ne ""} {
      if {![catch {uplevel 1 [concat [list ::_vibe_current_fileset_orig] $args]} r]} {
        return $r
      }
    }
    return "sim_1"
  }
}

proc ::vibe_xsim_gui::wrap_load_feature {} {
  if {[info commands ::load_feature] eq ""} {
    return
  }
  if {[info commands ::_vibe_load_feature_orig] ne ""} {
    return
  }
  rename ::load_feature ::_vibe_load_feature_orig
  proc ::load_feature {args} {
    set r [uplevel 1 [concat [list ::_vibe_load_feature_orig] $args]]
    ::vibe_xsim_gui::install_fileset_stub
    return $r
  }
}

::vibe_xsim_gui::wrap_load_feature
::vibe_xsim_gui::install_fileset_stub
puts "vibe_xsim_gui: current_fileset stub installed"
