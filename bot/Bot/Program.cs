using Bot.Calendar;
using Bot.Utils;
using dotenv.net;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Remora.Discord.Gateway.Extensions;
using Remora.Discord.Hosting.Extensions;
using System.Linq;
using System.Threading.Tasks;

namespace Bot {
    public class Program {
        public static Task Main(string[] args) {
            Config.CheckMinimalSettings();
            Database.Database.EnsureMigrationVersion(13);
            var hostBuilder = CreateHostBuilder(args);
            return hostBuilder.RunConsoleAsync();
        }

        private static IHostBuilder CreateHostBuilder(string[] args) => Host.CreateDefaultBuilder(args)
            .AddDiscordService(services => {
                return Config.BotToken;
            })
            .ConfigureServices(
                  (ctx, services) => {
                      services.AddSingleton(typeof(MessageAPIs));

                      var responderTypes = typeof(Program).Assembly
                          .GetExportedTypes()
                          .Where(t => t.IsResponder());
                      foreach (var responderType in responderTypes) {
                          services.AddResponder(responderType);
                      }
                  }
            )
            .ConfigureLogging(
                c => c
                    .AddConsole()
                    .AddFilter("System.Net.Http.HttpClient.*.LogicalHandler", LogLevel.Warning)
                    .AddFilter("System.Net.Http.HttpClient.*.ClientHandler", LogLevel.Warning)
            );
    }
}
