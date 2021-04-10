routes {
  * {
    sequence {
      App.init()

      /* App.setModal(Modal::LogIn) */
      if (@ENABLE_CALENDAR == "1") {
        Calendar.init()
      } else {
        Promise.never()
      }
    }
  }

  /admin {
    sequence {
      Window.setUrl("/")
      App.setModal(Modal::LogIn)
    }
  }

  /logout {
    sequence {
      Window.setUrl("/")
      App.logOut()
    }
  }
}
