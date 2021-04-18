record Event {
  time : String,
  name : String
}

store Calendar {
  state allMonthNames = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]

  state currentMonth = 0
  state currentYear = 0
  state today = Time.today()

  state daysData : Map(String, Array(Event)) = Map.empty()
  |> Map.set("28-3-2021", [Event("17:00", "Ants Green: GraczA vs graczB"), Event("18:00", "Ants Green: GraczA vs graczB"), Event("20:00", "Ants Green: GraczA vs graczB")])

  fun init {
    try {
      today =
        Time.today()

      next
        {
          currentMonth = Debug.log(Time.monthNum(today)),
          currentYear = Time.year(today),
          today = today
        }
    }
  }

  fun setPrevMonth {
    try {
      newMonth =
        Time.previousMonth(Time.from(currentYear, currentMonth, 1))

      next
        {
          currentYear = Debug.log(Time.year(newMonth)),
          currentMonth = Debug.log(Time.monthNum(newMonth))
        }
    }
  }

  fun setNextMonth {
    try {
      newMonth =
        Debug.log(Time.nextMonth(Time.from(currentYear, currentMonth, 1)))

      next
        {
          currentYear = Time.year(newMonth),
          currentMonth = Time.monthNum(newMonth)
        }
    }
  }

  fun daysInMonth (monthIndex : Number, year : Number) {
    `32 - new Date(#{year}, #{monthIndex}, 32).getDate()`
  }

  fun lastDaysFromPreviousMonth (curMonthNumber : Number, year : Number) : Array(Number) {
    try {
      curMonth =
        Time.from(year, curMonthNumber, 1)

      prevMonth =
        Time.previousMonth(curMonth)

      dayCount =
        daysInMonth(Time.monthNum(prevMonth) - 1, Time.year(prevMonth))

      firstDayThisMonth =
        `#{Time.startOf("month", curMonth)}.getDay()`

      if (firstDayThisMonth == 1) {
        []
      } else {
        Array.range(dayCount - firstDayThisMonth + 2, dayCount)
      }
    }
  }

  fun hashDate (day : Number, month : Number, year : Number) {
    "#{day}-#{month}-#{year}"
  }
}

component Page.Calendar {
  connect Calendar exposing { allMonthNames, today, currentMonth, currentYear }

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

    * {
      min-width: 100%;
    }
  }

  style day {
    display: flex;
    flex-direction: column;
    min-height: 100px;
    height: 100%;
    align-items: center;
    padding: 5px;
    border-bottom: 1px solid black;
    border-right: 1px solid black;

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

  style prev {
    color: #ccc;
  }

  style name {
    text-align: center;
    font-weight: bold;
  }

  style event {
    font-size: 0.8em;
    background-color: green;
    border-radius: 3px;
    color: white;
    padding: 0 3px;
    margin-bottom: 3px;
    font-weight: normal;
  }

  fun componentDidMount {
    if (@ENABLE_CALENDAR == "1") {
      Calendar.init()
    } else {
      Promise.never()
    }
  }

  fun render : Html {
    try {
      firstMonthDay =
        Time.from(currentYear, currentMonth, 1)

      <div::app>
        <div::currentMonth>
          <{ "#{allMonthNames[currentMonth - 1] or ""} #{currentYear}" }>

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
          for (day of ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]) {
            <div::name>
              <{ day }>
            </div>
          }

          for (day of Calendar.lastDaysFromPreviousMonth(currentMonth, currentYear)) {
            <div::day::prev>
              <{ "#{day}" }>

              <{ renderEvents(day, currentMonth - 1, currentYear) }>
            </div>
          }

          for (day of Time.range(firstMonthDay, Time.endOf("month", firstMonthDay))) {
            <div::day>
              <{ Time.format("d", day) }>

              <{ renderEvents(Time.dayNum(day), currentMonth, currentYear) }>
            </div>
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

      <div>
        for (evt of events) {
          <div::event>"#{evt.time}: #{evt.name}"</div>
        }
      </div>
    }
  }
}
