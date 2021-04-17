store App {
  state mainTab = if (@ENABLE_CALENDAR == "1") {
    MainTab::Calendar
  } else {
    MainTab::Matches
  }

  state loading = false
  state loggedInUser : Maybe(LoggedInUser) = Maybe::Nothing
  state modal : Modal = Modal::None

  fun init {
    checkUserAuth()
  }

  get hasAdminRole {
    case (loggedInUser) {
      Maybe::Just user => user.roles == 1
      => false
    }
    |> Debug.log
  }

  fun logIn (password : String) {
    sequence {
      sequence {
        App.setLoading(true)

        formData =
          FormData.empty()
          |> FormData.addString("password", password)

        response =
          Http.post("#{@ENDPOINT}/api/auth")
          |> Http.withCredentials(true)
          |> Http.formDataBody(formData)
          |> Http.send()

        if (response.status == 200) {
          sequence {
            loggedInUser =
              response.body
              |> Json.parse
              |> Maybe.andThen((json : Object) { Result.toMaybe(decode json as LoggedInUser) })

            next { loggedInUser = loggedInUser }

            App.setModal(Modal::None)
          }
        } else {
          `alert("Błędne hasło.")`
        }
      } catch Http.ErrorResponse => error {
        `alert("Sromotna klęska: " + JSON.stringify(#{error}))`
      }

      App.setLoading(false)
    }
  }

  fun logOut {
    sequence {
      Http.delete("#{@ENDPOINT}/api/auth")
      |> Http.withCredentials(true)
      |> Http.send()

      next { loggedInUser = Maybe::Nothing }

      void
    } catch Http.ErrorResponse => error {
      void
    }
  }

  fun checkUserAuth {
    sequence {
      response =
        "#{@ENDPOINT}/api/auth/check"
        |> Http.post()
        |> Http.withCredentials(true)
        |> Http.send()

      if (response.status == 200) {
        sequence {
          loggedInUser =
            response.body
            |> Json.parse
            |> Maybe.andThen((json : Object) { Result.toMaybe(decode json as LoggedInUser) })

          next { loggedInUser = loggedInUser }

          void
        }
      } else {
        Promise.never()
      }
    } catch Http.ErrorResponse => error {
      Promise.never()
    }
  }

  fun setMainTab (tab : MainTab) {
    next { mainTab = tab }
  }

  fun setLoading (enabled : Bool) {
    sequence {
      Timer.nextFrame()
      next { loading = enabled }
    }
  }

  fun setModal (modal : Modal) {
    next { modal = modal }
  }
}

enum MainTab {
  Calendar
  Matches
  NewMatch
}

enum Modal {
  None
  LogIn
}

record LoggedInUser {
  id : Number,
  roles : Number
}

record ServerError {
  error : String
}
