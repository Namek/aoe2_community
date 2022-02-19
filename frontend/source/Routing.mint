routes {
  / {
    sequence {
      App.init()

      if (@ENABLE_CALENDAR == "1") {
        Window.navigate("/#calendar")
      } else {
        Window.navigate("/#matches")
      }
    }
  }

  /#calendar {
    sequence {
      App.init()
      App.setMainTab(MainTab::Calendar)
    }
  }

  /#matches {
    sequence {
      App.init()
      App.setMainTab(MainTab::Matches)
    }
  }

  /#new-match {
    sequence {
      App.init()
      App.setMainTab(MainTab::NewMatch)
    }
  }

  /admin {
    sequence {
      App.init()
      Window.setUrl("/")
      App.setModal(Modal::LogIn)
    }
  }

  /logout {
    sequence {
      App.init()
      Window.setUrl("/")
      App.logOut()
    }
  }

  * {
    sequence {
      App.init()
      Window.navigate("/#calendar")
    }
  }
}
