import java.nio.file.*;
import org.antlr.v4.runtime.*;
import cc.ekblad.toml.parser.*;

class CheckToml {
    public static void main(String[] args) throws Exception {
        var failures = new java.util.concurrent.atomic.AtomicInteger();
        try (var paths = Files.walk(Path.of(args[0]))) {
            paths.filter(p -> p.toString().endsWith(".pw.toml")).toList().parallelStream().forEach(path -> {
                try {
                    var lexer = new TomlLexer(CharStreams.fromStream(new java.io.ByteArrayInputStream(Files.readAllBytes(path)), java.nio.charset.StandardCharsets.UTF_8));
                    var parser = new TomlParser(new CommonTokenStream(lexer));
                    parser.document();

                } catch (StackOverflowError | Exception error) {
                    System.out.println("FAIL " + path + " " + error.getClass().getSimpleName());
                    failures.incrementAndGet();
                }
            });
        }
        System.out.println("Parser failures: " + failures.get());
        if (failures.get() > 0) System.exit(1);
    }
}
