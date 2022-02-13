routes {
  / {
    sequence {
      App.init()
      Window.navigate("/#calendar")
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
