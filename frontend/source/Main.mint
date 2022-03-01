component Main {
  connect App exposing { mainTab, modal }

  fun closeModal {
    sequence {
      App.setModal(Modal::None)
    }
  }

  fun logIn {
    case (logInPasswordEl) {
      Maybe::Just(element) =>
        sequence {
          password =
            `#{element}.value`

          App.logIn(password)
        }

      => Promise.never()
    }
  }

  fun render : Html {
    <div::container>
      <div::main>
        <div class="tabs is-centered">
          <ul>
            if (@ENABLE_CALENDAR == "1") {
              <li
                class={Utils.whenStr(mainTab == MainTab::Calendar, "is-active")}
                onClick={(evt : Html.Event) { Window.navigate("/#calendar") }}>

                <a>"Kalendarz"</a>

              </li>
            }

            <li
              class={Utils.whenStr(mainTab == MainTab::Matches, "is-active")}
              onClick={(evt : Html.Event) { Window.navigate("/#matches") }}>

              <a>
                <span class="icon is-small">
                  <i
                    class="fas fa-list"
                    aria-hidden="true"/>
                </span>

                <span>"Mecze"</span>
              </a>

            </li>

            <li
              class={Utils.whenStr(mainTab == MainTab::NewMatch, "is-active")}
              onClick={(evt : Html.Event) { Window.navigate("/#new-match") }}>

              <a>
                <span class="icon is-small">
                  <i
                    class="fas fa-plus-circle"
                    aria-hidden="true"/>
                </span>

                <span>"Nowy mecz"</span>
              </a>

            </li>
          </ul>
        </div>

        case (mainTab) {
          MainTab::None =>
            <></>

          MainTab::Calendar =>
            <Page.Calendar/>

          MainTab::Matches =>
            <Page.Matches/>

          MainTab::NewMatch =>
            <Page.NewMatch/>
        }
      </div>

      case (modal) {
        Modal::None => <></>

        Modal::LogIn =>
          <div class="modal is-active">
            <div class="modal-background"/>

            <div class="modal-card">
              <header class="modal-card-head">
                <p class="modal-card-title">
                  "Panel admina"
                </p>

                <button
                  class="delete"
                  aria-label="close"
                  onClick={closeModal}/>
              </header>

              <section class="modal-card-body">
                <input as logInPasswordEl
                  type="password"
                  class="input"
                  name="password"
                  placeholder="Twoje prywatne hasło"
                  autofocus="autofocus"
                  onKeyDown={
                    (evt : Html.Event) {
                      if (evt.keyCode == 13) {
                        logIn()
                      } else {
                        Promise.never()
                      }
                    }
                  }/>
              </section>

              <footer class="modal-card-foot is-justify-content-flex-end">
                <button
                  class="button is-success"
                  onClick={logIn}>

                  "Zaloguj"

                </button>
              </footer>
            </div>
          </div>
      }

      if (App.loading) {
        <div::spinner>
          <span/>
        </div>
      }
    </div>
  }

  style container {
    position: relative;
    min-width: 100vw;
    min-height: 100vh;
    width: 100%;
    height: 100%;
  }

  style main {
    padding-top: 20px;
  }

  style spinner {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 100;
    background: rgba(0,0,0,0.9);
    text-align: center;
    user-select: none;

    span {
      position: absolute;
      bottom: 50%;

      display: inline-block;
      margin: auto;
      font-size: 25px;
      width: 1em;
      height: 1em;
      border-radius: 50%;
      text-indent: -9999em;
      -webkit-animation: load5 1.1s infinite ease;
      animation: load5 1.1s infinite ease;
      -webkit-transform: translateZ(0);
      -ms-transform: translateZ(0);
      transform: translateZ(0);
    }

    @keyframes load5 {
      0%,
      100% {
        box-shadow: 0em -2.6em 0em 0em #ffffff, 1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2), 2.5em 0em 0 0em rgba(255, 255, 255, 0.2), 1.75em 1.75em 0 0em rgba(255, 255, 255, 0.2), 0em 2.5em 0 0em rgba(255, 255, 255, 0.2), -1.8em 1.8em 0 0em rgba(255, 255, 255, 0.2), -2.6em 0em 0 0em rgba(255, 255, 255, 0.5), -1.8em -1.8em 0 0em rgba(255, 255, 255, 0.7);
      }

      12.5% {
        box-shadow: 0em -2.6em 0em 0em rgba(255, 255, 255, 0.7), 1.8em -1.8em 0 0em #ffffff, 2.5em 0em 0 0em rgba(255, 255, 255, 0.2), 1.75em 1.75em 0 0em rgba(255, 255, 255, 0.2), 0em 2.5em 0 0em rgba(255, 255, 255, 0.2), -1.8em 1.8em 0 0em rgba(255, 255, 255, 0.2), -2.6em 0em 0 0em rgba(255, 255, 255, 0.2), -1.8em -1.8em 0 0em rgba(255, 255, 255, 0.5);
      }

      25% {
        box-shadow: 0em -2.6em 0em 0em rgba(255, 255, 255, 0.5), 1.8em -1.8em 0 0em rgba(255, 255, 255, 0.7), 2.5em 0em 0 0em #ffffff, 1.75em 1.75em 0 0em rgba(255, 255, 255, 0.2), 0em 2.5em 0 0em rgba(255, 255, 255, 0.2), -1.8em 1.8em 0 0em rgba(255, 255, 255, 0.2), -2.6em 0em 0 0em rgba(255, 255, 255, 0.2), -1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2);
      }

      37.5% {
        box-shadow: 0em -2.6em 0em 0em rgba(255, 255, 255, 0.2), 1.8em -1.8em 0 0em rgba(255, 255, 255, 0.5), 2.5em 0em 0 0em rgba(255, 255, 255, 0.7), 1.75em 1.75em 0 0em #ffffff, 0em 2.5em 0 0em rgba(255, 255, 255, 0.2), -1.8em 1.8em 0 0em rgba(255, 255, 255, 0.2), -2.6em 0em 0 0em rgba(255, 255, 255, 0.2), -1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2);
      }

      50% {
        box-shadow: 0em -2.6em 0em 0em rgba(255, 255, 255, 0.2), 1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2), 2.5em 0em 0 0em rgba(255, 255, 255, 0.5), 1.75em 1.75em 0 0em rgba(255, 255, 255, 0.7), 0em 2.5em 0 0em #ffffff, -1.8em 1.8em 0 0em rgba(255, 255, 255, 0.2), -2.6em 0em 0 0em rgba(255, 255, 255, 0.2), -1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2);
      }

      62.5% {
        box-shadow: 0em -2.6em 0em 0em rgba(255, 255, 255, 0.2), 1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2), 2.5em 0em 0 0em rgba(255, 255, 255, 0.2), 1.75em 1.75em 0 0em rgba(255, 255, 255, 0.5), 0em 2.5em 0 0em rgba(255, 255, 255, 0.7), -1.8em 1.8em 0 0em #ffffff, -2.6em 0em 0 0em rgba(255, 255, 255, 0.2), -1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2);
      }

      75% {
        box-shadow: 0em -2.6em 0em 0em rgba(255, 255, 255, 0.2), 1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2), 2.5em 0em 0 0em rgba(255, 255, 255, 0.2), 1.75em 1.75em 0 0em rgba(255, 255, 255, 0.2), 0em 2.5em 0 0em rgba(255, 255, 255, 0.5), -1.8em 1.8em 0 0em rgba(255, 255, 255, 0.7), -2.6em 0em 0 0em #ffffff, -1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2);
      }

      87.5% {
        box-shadow: 0em -2.6em 0em 0em rgba(255, 255, 255, 0.2), 1.8em -1.8em 0 0em rgba(255, 255, 255, 0.2), 2.5em 0em 0 0em rgba(255, 255, 255, 0.2), 1.75em 1.75em 0 0em rgba(255, 255, 255, 0.2), 0em 2.5em 0 0em rgba(255, 255, 255, 0.2), -1.8em 1.8em 0 0em rgba(255, 255, 255, 0.5), -2.6em 0em 0 0em rgba(255, 255, 255, 0.7), -1.8em -1.8em 0 0em #ffffff;
      }
    }
  }
}
