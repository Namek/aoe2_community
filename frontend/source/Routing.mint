routes {
  / {
    sequence {
      App.init()
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
}
