class Options
  attr_reader :options

  def self.parse_args
    return @options if @options

    @options = {}
    optparse = OptionParser.new do|opts|
      # Set a banner
      opts.banner = "Usage: harness.rb [options...]"

      @options[:tests] = []
      opts.on( '-t', '--tests DIR/FILE', 'Execute tests in DIR or FILE (defaults to "./tests")' ) do|dir|
        @options[:tests] << dir
      end

      @options[:type] = 'skip'
      opts.on('--type TYPE', 'Select puppet install type (pe, pe_ro, git, skip) - default "skip"') do |type|
        unless File.directory?("setup/#{type}") then
          Log.error "Sorry, #{type} is not a known setup type!"
          exit 1
        end
        @options[:type] = type
      end

      @options[:puppet] = 'git://github.com/puppetlabs/puppet.git#HEAD'
      opts.on('-p', '--puppet URI', 'Select puppet git install URI',
              "  #{@options[:puppet]}",
              "    - URI and revision, default HEAD",
              "  just giving the revision is also supported"
              ) do |value|
        @options[:type] = 'git'
        @options[:puppet] = value
      end

      @options[:facter] = 'git://github.com/puppetlabs/facter.git#HEAD'
      opts.on('-f', '--facter URI', 'Select facter git install URI',
              "  #{@options[:facter]}",
              "    - otherwise, as per the puppet argument"
              ) do |value|
        @options[:type] = 'git'
        @options[:facter] = value
      end

      @options[:plugins] = []
      opts.on('--plugin URI', 'Select puppet plugin git install URI') do |value|
        @options[:type] = 'git'
        @options[:plugins] << value
      end

      @options[:config] = nil
      opts.on( '-c', '--config FILE', 'Use configuration FILE' ) do|file|
        @options[:config] = file
      end

      opts.on( '--debug', 'Enable full debugging' ) do |enable_debug|
        if enable_debug
          Log.log_level = :debug
        else
          Log.log_level = :normal
        end
      end

      opts.on( '-d', '--dry-run', "Just report what would be done on the targets" ) do |file|
        $dry_run = true
      end

      @options[:vmrun] = FALSE
      opts.on( '--vmrun', 'VM revert and start VMs' ) do
        @options[:vmrun] = @options[:type]
      end

      @options[:mrpropper] = FALSE
      opts.on( '--mrpropper', 'Clean hosts' ) do
        @options[:mrpropper] = TRUE
      end

      @options[:notimesync] = FALSE
      opts.on( '--notimesync', 'skip ntpdate step' ) do
        @options[:notimesync] = TRUE
      end

      @options[:stdout_only] = false
      opts.on('-s', '--stdout-only', 'log output to STDOUT but no files') do
        @options[:stdout_only] = true
      end

      Log.stdout = true
      opts.on('-q', '--quiet', 'don\'t log output to STDOUT') do
        Log.stdout = false
        @options[:quiet] = true
      end

      Log.color = true
      opts.on('--[no-]color', 'don\'t display color in log output') do |value|
        Log.color = value
      end

      @options[:random] = false
      opts.on('-r', '--random [RANDOM_KEY]', 'Randomize ordering of test files') do |random_key|
        @options[:random] = random_key || true
      end

      @options[:xml] = false
      opts.on('-x', '--[no-]xml', 'Emit JUnit XML reports on tests') do |value|
        @options[:xml] = value
      end

      opts.on( '-h', '--help', 'Display this screen' ) do
        puts opts
        exit
      end
    end
    optparse.parse!

    @options[:tests] << 'tests' if @options[:tests].empty?

    @options
  end
end