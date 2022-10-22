component Page.Matches {
  connect App exposing { loggedInUser }
  connect Matches exposing { matches }

  state sortingMode = SortingMode::DateDesc
  state watchStatusFilter : Maybe(Number) = Maybe::Nothing

  fun componentDidMount {
    Matches.refreshList()
  }

  fun toggleSortMode {
    next
      {
        sortingMode =
          case (sortingMode) {
            SortingMode::DateDesc => SortingMode::DateAsc
            SortingMode::DateAsc => SortingMode::IdDesc
            SortingMode::IdDesc => SortingMode::DateDesc
          }
      }
  }

  fun matchSortFn (m1 : Match, m2 : Match) {
    case (sortingMode) {
      SortingMode::IdDesc => m2.id - m1.id

      SortingMode::DateAsc =>
        m1.date - m2.date

      SortingMode::DateDesc =>
        m2.date - m1.date
    }
  }

  fun render : Html {
    <div::app>
      case (matches) {
        Maybe::Just(result) =>
          case (result) {
            Result::Ok(ms) =>
              if (Array.size(ms) == 0) {
                <p>"Brak meczy."</p>
              } else {
                renderMatchesTable(ms)
              }

            Result::Err(err) =>
              <p>
                <{ err }>
              </p>
          }

        Maybe::Nothing => <p>"Ładowanie..."</p>
      }
    </div>
  }

  fun renderMatchesTable (matches : Array(Match)) : Html {
    <table class="table is-hoverable is-narrow">
      <thead>
        <tr>
          <th onClick={toggleSortMode}>
            "Data "

            if (sortingMode == SortingMode::DateAsc) {
              "↓"
            }

            if (sortingMode == SortingMode::DateDesc) {
              "↑"
            }
          </th>

          <th>"Grupa"</th>
          <th>"Draft"</th>
          <th>"Nagrania"</th>

          <th>
            "Status "

            if (App.hasAdminRole) {
              <div class="select is-small">
                <select
                  value={
                    (watchStatusFilter
                    |> Maybe.map(Number.toString)) or ""
                  }
                  onChange={
                    (evt : Html.Event) {
                      try {
                        value =
                          Number.fromString(`#{evt.target}.value`)

                        next { watchStatusFilter = value }
                      }
                    }
                  }>

                  <option value="">
                    "wszystkie"
                  </option>

                  <option value={Number.toString(Matches:WATCH_STATUS_UNTOUCHED)}>
                    "❌ Nietknięty"
                  </option>

                  <option value={Number.toString(Matches:WATCH_STATUS_WATCHED)}>
                    "👀 Obejrzany"
                  </option>

                  <option value={Number.toString(Matches:WATCH_STATUS_TO_BE_COMMENTED_SOON)}>
                    "🗣️📢 Komentarz wkrótce"
                  </option>

                  <option value={Number.toString(Matches:WATCH_STATUS_WATCHED_AND_NOTED)}>
                    "📝 Wpisany"
                  </option>

                  <option value={Number.toString(Matches:WATCH_STATUS_COMMENTED)}>
                    "📺 Skomentowany"
                  </option>

                </select>
              </div>
            }
          </th>
        </tr>
      </thead>

      <tbody>
        for (match of Array.sort(matchSortFn, matches)) {
          if (Maybe.isNothing(watchStatusFilter) || watchStatusFilter == Maybe::Just(match.watchStatus)) {
            renderMatch(match)
          } else {
            <>""</>
          }
        }
      </tbody>
    </table>
  }

  fun renderMatch (match : Match) : Html {
    <tr>
      <td>"#{Utils.epochToDateString(match.date)}"</td>
      <td>"#{match.group} (BO#{match.bestOf})"</td>

      <td>
        <{ renderDraft(match) }>
      </td>

      <td>
        for (rec of match.recordings
        |> Array.mapWithIndex((rec : Recording, i : Number) { {rec, i} })) {
          <>
            <a
              href="#{@ENDPOINT}/api/match/#{match.id}/recording/#{rec[0].id}"
              target="_blank"
              rel="noopener noreferrer">

              "##{rec[1] + 1}"

            </a>

            " "
          </>
        }
      </td>

      <td>
        if (App.hasAdminRole) {
          <>
            <div class="select">
              <select
                value={Number.toString(match.watchStatus)}
                onChange={
                  (evt : Html.Event) {
                    Matches.setWatchStatus(match, `+#{evt.target}.value`)
                  }
                }>

                <option value={Number.toString(Matches:WATCH_STATUS_UNTOUCHED)}>
                  "❌ Nietknięty"
                </option>

                <option value={Number.toString(Matches:WATCH_STATUS_WATCHED)}>
                  "👀 Obejrzany"
                </option>

                <option value={Number.toString(Matches:WATCH_STATUS_TO_BE_COMMENTED_SOON)}>
                  "🗣️📢 Komentarz wkrótce"
                </option>

                <option value={Number.toString(Matches:WATCH_STATUS_WATCHED_AND_NOTED)}>
                  "📝 Wpisany"
                </option>

                <option value={Number.toString(Matches:WATCH_STATUS_COMMENTED)}>
                  "📺 Skomentowany"
                </option>

              </select>
            </div>

            <br/>
            <br/>

            <button
              class="button is-danger is-small"
              onClick={() { Matches.deleteMatch(match) }}>

              <span>"Usuń mecz"</span>

            </button>
          </>
        } else {
          <span>
            case (match.watchStatus) {
              Matches:WATCH_STATUS_WATCHED => "👀 Obejrzany"
              Matches:WATCH_STATUS_WATCHED_AND_NOTED => "📝 Wpisany"
              Matches:WATCH_STATUS_TO_BE_COMMENTED_SOON => "🗣️📢 Komentarz wkrótce"
              Matches:WATCH_STATUS_COMMENTED => "📺 Skomentowany"
              => ""
            }
          </span>
        }
      </td>
    </tr>
  }

  fun renderDraft (match : Match) : Html {
    <table::draft class="table is-bordered is-narrow is-fullwidth">
      <thead>
        <tr>
          <td>
            if (String.isNotBlank(civDraft)) {
              <a
                href="https://aoe2cm.net/draft/#{civDraft}"
                rel="noopener noreferrer"
                target="_blank">

                "Civ Draft"

              </a>
            }
          </td>

          <td>"#{match.p0Name}"</td>
          <td>"#{match.p1Name}"</td>
        </tr>
      </thead>

      <tbody>
        if (String.isNotBlank(p0MapBan) || String.isNotBlank(p1MapBan)) {
          <tr>
            <th class="tooltip-parent">
              "🗺️🚫"

              <div class="tooltip">
                <span class="tooltiptext">
                  "map bans"
                </span>
              </div>
            </th>

            <td>"#{p0MapBan}"</td>
            <td>"#{p1MapBan}"</td>
          </tr>
        }

        <tr>
          <th class="tooltip-parent">
            "🗺️🏠"

            <div class="tooltip">
              <span class="tooltiptext">
                "home maps"
              </span>
            </div>
          </th>

          <td>
            "#{match.p0Maps
            |> String.join(", ")}"
          </td>

          <td>
            "#{match.p1Maps
            |> String.join(", ")}"
          </td>
        </tr>

        if (!Array.isEmpty(match.p0CivBans)) {
          <tr>
            <th class="tooltip-parent">
              "🏘️🚫"

              <div class="tooltip">
                <span class="tooltiptext">
                  "civ bans"
                </span>
              </div>
            </th>

            <td>
              "#{match.p0CivBans
              |> String.join(", ")}"
            </td>

            <td>
              "#{match.p1CivBans
              |> String.join(", ")}"
            </td>
          </tr>
        }
      </tbody>
    </table>
  } where {
    civDraft =
      match.civDraft or ""

    p0MapBan =
      match.p0MapBan or ""

    p1MapBan =
      match.p1MapBan or ""
  }

  style app {
    display: flex;
    justify-content: center;

    table {
      margin: 0 auto;

      th {
        user-select: none;
      }
    }
  }

  style draft {
    td:nth-child(1) {
      text-align: center;
      min-width: 50px;
    }

    tr > *:nth-child(2) {
      width: 180px;
    }

    tr > *:nth-child(3) {
      width: 180px;
    }
  }
}
