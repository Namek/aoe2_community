component Page.Calendar {
  const MONTH_NAMES = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
  const DAY_NAMES = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]

  connect Calendar exposing { today, currentMonth, currentYear, currentDay }

  style app {
    justify-content: center;
    flex-direction: column;
    align-items: center;
    display: flex;
  }

  style currentMonth {
    font-size: 2em;
    margin-bottom: 1em;
    text-align: center;
    font-weight: bold;
  }

  style month {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr 1fr;
    grid-template-rows: auto;

    max-width: 90vw;
    width: 100%;
    justify-items: center;
    align-items: center;

    > * {
      min-width: 100%;
    }
  }

  style day (isToday : Bool) {
    display: flex;
    flex-direction: column;
    min-height: 100px;
    height: 100%;
    align-items: center;
    padding: 5px;
    border-bottom: 1px solid black;
    border-right: 1px solid black;
    overflow: visible;

    if (isToday) {
      background-color: #6083AE;
      color: black;
    }

    &:nth-child(7n + 1) {
      border-left: 1px solid black;
    }

    &:nth-child(8) {
      border-top-left-radius: 5px;
    }

    &:nth-child(8),
    &:nth-child(9),
    &:nth-child(10),
    &:nth-child(11),
    &:nth-child(12),
    &:nth-child(13),
    &:nth-child(14) {
      border-top: 1px solid black;
    }

    &:nth-child(14) {
      border-top-right-radius: 5px;
    }

    &:last-child {
      border-bottom-right-radius: 5px;
    }
  }

  style dayEvents {
    width: 100%;
  }

  style prev {
    color: #ccc;
  }

  style name {
    text-align: center;
    font-weight: bold;
  }

  style event (colorId : Number) {
    position: relative;
    font-size: 0.8em;

    if (colorId == 1) {
      background-color: #334A61;
    } else {
      background-color: #476787;
    }

    border-radius: 3px;
    color: white;
    padding: 0 3px;
    margin-bottom: 3px;
    font-weight: normal;
    white-space: pre-wrap;
    word-break: break-word;

    &:hover {
      background-color: #547AA0;
      color: black;
    }

    a {
      color: black;
      text-decoration: underline;

      &:hover {
        color: #555;
        text-decoration: none;
      }
    }
  }

  style tooltip {
    word-break: keep-all;
  }

  style eventTime {
    width: 100%;
    color: #ddd;
    float: left;
  }

  style channelIcon {
    position: absolute;
    right: 5px;
    width: 20px;
    height: 20px;
    bottom: calc(50% - 10px);
  }

  fun render : Html {
    try {
      firstMonthDay =
        Time.from(currentYear, currentMonth, 1)

      todayMonthNum =
        Time.monthNum(today)

      todayDayNum =
        Time.dayNum(today)

      todayYear =
        Time.year(today)

      isTodayYear =
        currentYear == todayYear

      <div::app>
        <div::currentMonth>
          <{ "#{MONTH_NAMES[currentMonth - 1] or ""} #{currentYear}" }>

          <div>
            <button onClick={Calendar.setPrevMonth}>
              "<"
            </button>

            <button onClick={Calendar.setNextMonth}>
              ">"
            </button>
          </div>
        </div>

        <div::month>
          for (day of DAY_NAMES) {
            <div::name>
              <{ day }>
            </div>
          }

          for (day of Calendar.lastDaysFromPreviousMonth(currentMonth, currentYear)) {
            try {
              isToday =
                day == todayDayNum && currentMonth - 1 == todayMonthNum && isTodayYear

              <div::day(isToday)::prev>
                <{ "#{day}" }>

                <{ renderEvents(day, currentMonth - 1, currentYear) }>
              </div>
            }
          }

          for (day of Time.range(firstMonthDay, Time.endOf("month", firstMonthDay))) {
            try {
              isToday =
                Time.dayNum(day) == currentDay && Time.monthNum(day) == todayMonthNum && isTodayYear

              <div::day(isToday)>
                <{ Time.format("d", day) }>

                <{ renderEvents(Time.dayNum(day), currentMonth, currentYear) }>
              </div>
            }
          }
        </div>
      </div>
    }
  }

  fun renderEvents (day : Number, givenMonth : Number, givenYear : Number) : Html {
    try {
      {month, year} =
        if (givenMonth == 0) {
          {12, givenYear - 1}
        } else {
          {givenMonth, givenYear}
        }

      hash =
        Calendar.hashDate(day, month, year)

      events =
        Map.get(hash, Calendar.daysData) or []

      <div::dayEvents>
        for (evt of events) {
          <div::event(evt.sourceId) class="tooltip-parent">
            <span::eventTime>
              <{ Time.format("HH:mm", evt.datetime) }>
            </span>

            "#{evt.name}"

            case (evt.spectate) {
              SpectateMode::OnChannel(link) =>
                <div::channelIcon>"🔴"</div>

              SpectateMode::Offline =>
                <div::channelIcon>"❌"</div>

              => <></>
            }

            if (App.hasAdminRole) {
              <div::tooltip class="tooltip">
                <span class="tooltiptext">
                  <button onClick={() { toggleSpectateMode(evt) }}>
                    case (evt.spectate) {
                      SpectateMode::OnChannel(link) => "🔴"
                      SpectateMode::Offline => "❌"
                      SpectateMode::Unknown => "?"
                    }
                  </button>

                  case (evt.spectate) {
                    SpectateMode::OnChannel(link) =>
                      <>
                        "Mecz komentowany na żywo:"
                        <br/>

                        <input as spectateLinkEl
                          type="text"
                          placeholder="linki oddzielone ||"
                          value={
                            case (evt.spectate) {
                              SpectateMode::OnChannel(link) => link
                              => ""
                            }
                          }
                          onBlur={
                            () {
                              case (spectateLinkEl) {
                                Maybe::Just(el) =>
                                  sequence {
                                    oldValue =
                                      case (evt.spectate) {
                                        SpectateMode::OnChannel(link) => link
                                        => ""
                                      }

                                    `#{el}.value = #{oldValue}`
                                  }

                                =>
                                  Promise.never()
                              }
                            }
                          }
                          onKeyDown={
                            (keyEvt : Html.Event) {
                              if (keyEvt.keyCode == 13) {
                                sequence {
                                  case (spectateLinkEl) {
                                    Maybe::Just(el) =>
                                      saveSpectateLink(evt, `#{el}.value`)

                                    =>
                                      Promise.never()
                                  }
                                }
                              } else {
                                Promise.never()
                              }
                            }
                          }/>
                      </>

                    SpectateMode::Offline =>
                      <>
                        "Mecz offline:"
                        <br/>
                        "Spectators off"
                      </>

                    SpectateMode::Unknown =>
                      <>
                        "(Nie wiadomo czy będzie online, offline lub komentowany)"
                      </>
                  }
                </span>
              </div>
            } else {
              case (evt.spectate) {
                SpectateMode::OnChannel(links) =>
                  <div::tooltip class="tooltip">
                    <span class="tooltiptext">
                      "Mecz komentowany na żywo:"
                      <br/>

                      for (link of splitLinks(links)) {
                        <a href="#{link}">
                          "#{link}"
                          <br/>
                        </a>
                      }
                    </span>
                  </div>

                SpectateMode::Offline =>
                  <div::tooltip class="tooltip">
                    <span class="tooltiptext">
                      "Mecz nie na żywo."
                      <br/>
                      "Spectate off."
                    </span>
                  </div>

                SpectateMode::Unknown => <></>
              }
            }
          </div>
        }
      </div>
    }
  }

  fun splitLinks (links : String) : Array(String) {
    links
    |> String.split("||")
    |> Array.map(String.trim)
  }

  fun toggleSpectateMode (evt : Event) {
    sequence {
      newSpectMode =
        case (evt.spectate) {
          SpectateMode::Unknown => Maybe::Just(true)
          SpectateMode::OnChannel(link) => Maybe::Just(false)
          SpectateMode::Offline => Maybe::Nothing
        }

      newSpectLink =
        if (newSpectMode == Maybe::Just(true)) {
          Maybe::Just("")
        } else {
          Maybe::Nothing
        }

      Calendar.setSpectateMode(evt.id, newSpectMode, newSpectLink)
    }
  }

  fun saveSpectateLink (evt : Event, link : String) {
    Calendar.setSpectateMode(evt.id, Maybe::Just(true), Maybe::Just(link))
  }
}
